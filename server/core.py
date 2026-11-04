"""Trips, Gmail sync, and WhatsApp dispatch logic."""
import json
import os
import re
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta
from email.utils import parsedate_to_datetime
from zoneinfo import ZoneInfo

import db
import gmail

TZ = ZoneInfo(os.environ.get("STARK_TZ", "Asia/Kolkata"))
SEG_FIELDS = ["type", "status", "status_label", "origin", "destination", "date", "start_time",
              "end_date", "end_time", "carrier", "number", "reference", "details"]
SEG_TYPES = {"flight", "train", "bus", "cab", "hotel", "other"}
SEG_STATUSES = {"reserved", "confirmed", "waitlisted", "delayed", "completed", "cancelled"}
STATUS_WORD = {"reserved": "Reserved", "confirmed": "Confirmed", "waitlisted": "Waitlisted",
               "delayed": "Delayed", "completed": "Completed", "cancelled": "Cancelled"}
TYPE_WORD = {"flight": "Flight", "train": "Train", "bus": "Bus", "cab": "Cab", "hotel": "Hotel stay", "other": "Booking"}

sync_lock = threading.Lock()


# ---------------------------------------------------------------- helpers

def today():
    return datetime.now(TZ).date()


def seg_start(s):
    if not s.get("date"):
        return None
    try:
        d = date.fromisoformat(s["date"])
        hh, mm = (s.get("start_time") or "00:00").split(":")[:2]
        return datetime(d.year, d.month, d.day, int(hh), int(mm), tzinfo=TZ)
    except (ValueError, TypeError):
        return None


def seg_end(s):
    d = s.get("end_date") or s.get("date")
    if not d:
        return None
    try:
        d = date.fromisoformat(d)
        t = s.get("end_time") or s.get("start_time") or "23:59"
        hh, mm = t.split(":")[:2]
        return datetime(d.year, d.month, d.day, int(hh), int(mm), tzinfo=TZ)
    except (ValueError, TypeError):
        return None


def trip_phase(trip, segs):
    """upcoming | ongoing | completed | cancelled — derived from segment dates and statuses."""
    if trip.get("cancelled") or (segs and all(s["status"] == "cancelled" for s in segs)):
        return "cancelled"
    live = [s for s in segs if s["status"] != "cancelled"]
    if not live:
        return "upcoming"
    now = datetime.now(TZ)
    starts = [x for x in (seg_start(s) for s in live) if x]
    ends = [x for x in (seg_end(s) for s in live) if x]
    if all(s["status"] == "completed" for s in live) or (ends and max(ends) < now and len(ends) == len(live)):
        return "completed"
    if starts and min(starts) <= now:
        return "ongoing"
    return "upcoming"


def clean_seg(s):
    out = {}
    for k in SEG_FIELDS:
        v = s.get(k)
        out[k] = (str(v).strip() if v is not None else None)
    out["type"] = out["type"] if out["type"] in SEG_TYPES else "other"
    out["status"] = out["status"] if out["status"] in SEG_STATUSES else "confirmed"
    for k in ("date", "end_date"):
        if out[k] and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", out[k]):
            out[k] = None
    for k in ("start_time", "end_time"):
        if out[k]:
            m = re.fullmatch(r"(\d{1,2}):(\d{2})", out[k])
            out[k] = f"{int(m.group(1)):02d}:{m.group(2)}" if m else None
    for k in ("status_label", "origin", "destination", "carrier", "number", "reference", "details"):
        out[k] = (out[k] or "")[:300]
    return out


HONORIFICS = {"mr", "mrs", "ms", "miss", "dr", "master", "shri", "smt", "sri", "kum", "prof"}


def norm_name(n):
    toks = re.sub(r"[^a-z ]", " ", (n or "").lower()).split()
    return [t for t in toks if t not in HONORIFICS]


def same_person(a, b, travelers=None):
    x, y = norm_name(a), norm_name(b)
    if not x or not y:
        return False
    if x == y or (len(x) >= 2 and len(y) >= 2 and x[0] == y[0] and x[-1] == y[-1]):
        return True
    if travelers:
        ta, tb = match_traveler(a, travelers), match_traveler(b, travelers)
        return bool(ta and tb and ta["id"] == tb["id"])
    return False


def match_traveler(name, travelers):
    """Directory entry for a printed passenger name (exact, alias, or same first+last tokens)."""
    want = norm_name(name)
    if not want:
        return None
    for t in travelers:
        names = [t["name"]] + [a for a in (t.get("aliases") or "").split(",") if a.strip()]
        for n in names:
            have = norm_name(n)
            if have == want:
                return t
            if len(have) >= 2 and len(want) >= 2 and have[0] == want[0] and have[-1] == want[-1]:
                return t
            if len(want) == 1 and have and want[0] == have[0] and len(names) == 1 and len(have) == 1:
                return t
    return None


# ---------------------------------------------------------------- reads

def load_trip(trip_id):
    t = db.one("SELECT * FROM trips WHERE id = ?", (trip_id,))
    if not t:
        return None
    return decorate(t)


def decorate(t, segs=None, travelers=None, counts=None, lastwa=None):
    if segs is None:
        segs = db.rows("SELECT * FROM segments WHERE trip_id = ? ORDER BY position, date, start_time", (t["id"],))
    if travelers is None:
        travelers = db.rows("SELECT * FROM travelers")
    names = json.loads(t["travelers"] or "[]")
    t = dict(t)
    t["travelers"] = [{"name": n, "phone": (m or {}).get("phone", ""), "traveler_id": (m or {}).get("id")}
                      for n, m in ((n, match_traveler(n, travelers)) for n in names)]
    t["segments"] = segs
    t["phase"] = trip_phase(t, segs)
    t["modes"] = sorted({s["type"] for s in segs})
    starts = [s["date"] for s in segs if s.get("date")]
    t["first_date"] = min(starts) if starts else None
    t["last_date"] = max([s.get("end_date") or s.get("date") for s in segs if s.get("date")] or [None]) if starts else None
    if counts is None:
        r = db.one("SELECT COUNT(*) n FROM log WHERE trip_id = ?", (t["id"],))
        counts = r["n"] if r else 0
    t["log_count"] = counts
    if lastwa is None:
        lastwa = db.one("SELECT at, state, trigger, error FROM wa_messages WHERE trip_id = ? ORDER BY id DESC LIMIT 1", (t["id"],))
    t["last_whatsapp"] = lastwa
    return t


def list_trips():
    trips = db.rows("SELECT * FROM trips ORDER BY created_at DESC")
    segs = db.rows("SELECT * FROM segments ORDER BY position, date, start_time")
    by_trip = {}
    for s in segs:
        by_trip.setdefault(s["trip_id"], []).append(s)
    travelers = db.rows("SELECT * FROM travelers")
    counts = {r["trip_id"]: r["n"] for r in db.rows("SELECT trip_id, COUNT(*) n FROM log GROUP BY trip_id")}
    lastwa = {}
    for r in db.rows("SELECT trip_id, at, state, trigger, error FROM wa_messages WHERE id IN "
                     "(SELECT MAX(id) FROM wa_messages GROUP BY trip_id)"):
        lastwa[r["trip_id"]] = r
    out = [decorate(t, by_trip.get(t["id"], []), travelers, counts.get(t["id"], 0), lastwa.get(t["id"])) for t in trips]
    return out


# ---------------------------------------------------------------- writes

def save_trip(trip_id, data, actor):
    """Create (trip_id None) or update a trip with its full segment list. Returns (trip_id, status_changes)."""
    title = (data.get("title") or "").strip()[:200] or "Untitled trip"
    names = [n.strip()[:120] for n in data.get("travelers", []) if isinstance(n, str) and n.strip()][:20]
    segs = [clean_seg(s) for s in data.get("segments", [])][:30]
    keep_ids = [s.get("id") for s in data.get("segments", [])]
    changes = []
    with db.tx() as c:
        if trip_id is None:
            trip_id = db.new_id()
            c.execute("INSERT INTO trips(id, title, travelers, cancelled, notes, source, created_at, updated_at) "
                      "VALUES(?,?,?,?,?,?,?,?)", (trip_id, title, json.dumps(names), int(bool(data.get("cancelled"))),
                                                   data.get("notes", "")[:2000], data.get("source", "manual"), db.now(), db.now()))
            db.add_log(trip_id, actor, "created", f"Trip created: {title}", c)
            old = {}
        else:
            prev = c.execute("SELECT * FROM trips WHERE id = ?", (trip_id,)).fetchone()
            if not prev:
                raise KeyError(trip_id)
            old = {r["id"]: dict(r) for r in c.execute("SELECT * FROM segments WHERE trip_id = ?", (trip_id,))}
            edits = []
            if prev["title"] != title:
                edits.append(f"title → “{title}”")
            if json.loads(prev["travelers"]) != names:
                edits.append("travellers → " + (", ".join(names) or "none"))
            if bool(prev["cancelled"]) != bool(data.get("cancelled")):
                edits.append("trip cancelled" if data.get("cancelled") else "trip reinstated")
            c.execute("UPDATE trips SET title=?, travelers=?, cancelled=?, notes=?, updated_at=? WHERE id=?",
                      (title, json.dumps(names), int(bool(data.get("cancelled"))), data.get("notes", prev["notes"])[:2000], db.now(), trip_id))
            if edits:
                db.add_log(trip_id, actor, "edit", "Edited " + "; ".join(edits), c)
        seen = set()
        for i, (s, sid) in enumerate(zip(segs, keep_ids)):
            if sid and sid in old:
                o = old[sid]
                diff = [k for k in SEG_FIELDS if (o.get(k) or None) != (s.get(k) or None)]
                if diff:
                    c.execute("UPDATE segments SET position=?, " + ", ".join(f"{k}=?" for k in SEG_FIELDS) + " WHERE id=?",
                              [i] + [s[k] for k in SEG_FIELDS] + [sid])
                    label = f"{TYPE_WORD[s['type']]} {s['origin']} → {s['destination']}"
                    if "status" in diff:
                        changes.append(sid)
                        db.add_log(trip_id, actor, "status", f"{label}: {STATUS_WORD[o['status']]} → {STATUS_WORD[s['status']]}", c)
                    other = [k for k in diff if k not in ("status", "status_label")]
                    if other:
                        db.add_log(trip_id, actor, "edit", f"{label}: updated {', '.join(k.replace('_', ' ') for k in other)}", c)
                elif o["position"] != i:
                    c.execute("UPDATE segments SET position=? WHERE id=?", (i, sid))
                seen.add(sid)
            else:
                nid = db.new_id()
                c.execute("INSERT INTO segments(id, trip_id, position, " + ", ".join(SEG_FIELDS) + ", email_id) VALUES(?,?,?," +
                          ",".join("?" * len(SEG_FIELDS)) + ",?)", [nid, trip_id, i] + [s[k] for k in SEG_FIELDS] + [data.get("email_id")])
                if old or data.get("log_added", True):
                    db.add_log(trip_id, actor, "segment", f"Added {TYPE_WORD[s['type']].lower()} {s['origin']} → {s['destination']}"
                               + (f" on {s['date']}" if s['date'] else ""), c)
        for sid, o in old.items():
            if sid not in seen:
                c.execute("DELETE FROM segments WHERE id = ?", (sid,))
                db.add_log(trip_id, actor, "segment", f"Removed {TYPE_WORD.get(o['type'], 'segment').lower()} {o['origin']} → {o['destination']}", c)
    return trip_id, changes


def merge_trips(src_id, dst_id, actor):
    if src_id == dst_id:
        raise ValueError("Pick a different trip to merge into.")
    with db.tx() as c:
        src = c.execute("SELECT * FROM trips WHERE id=?", (src_id,)).fetchone()
        dst = c.execute("SELECT * FROM trips WHERE id=?", (dst_id,)).fetchone()
        if not src or not dst:
            raise KeyError("trip")
        n = c.execute("SELECT COALESCE(MAX(position), -1) + 1 FROM segments WHERE trip_id=?", (dst_id,)).fetchone()[0]
        for i, r in enumerate(c.execute("SELECT id FROM segments WHERE trip_id=? ORDER BY position", (src_id,)).fetchall()):
            c.execute("UPDATE segments SET trip_id=?, position=? WHERE id=?", (dst_id, n + i, r["id"]))
        names = json.loads(dst["travelers"])
        for x in json.loads(src["travelers"]):
            if x not in names:
                names.append(x)
        c.execute("UPDATE trips SET travelers=?, updated_at=? WHERE id=?", (json.dumps(names), db.now(), dst_id))
        c.execute("UPDATE log SET trip_id=? WHERE trip_id=?", (dst_id, src_id))
        c.execute("UPDATE wa_messages SET trip_id=? WHERE trip_id=?", (dst_id, src_id))
        c.execute("UPDATE emails SET trip_id=? WHERE trip_id=?", (dst_id, src_id))
        c.execute("DELETE FROM trips WHERE id=?", (src_id,))
        db.add_log(dst_id, actor, "merge", f"Merged “{src['title']}” into this trip", c)


def delete_trip(trip_id):
    with db.tx() as c:
        c.execute("DELETE FROM segments WHERE trip_id=?", (trip_id,))
        c.execute("DELETE FROM trips WHERE id=?", (trip_id,))
        c.execute("DELETE FROM log WHERE trip_id=?", (trip_id,))
        c.execute("UPDATE emails SET trip_id=NULL WHERE trip_id=?", (trip_id,))


# ---------------------------------------------------------------- WhatsApp

def fmt_date(d):
    try:
        x = date.fromisoformat(d)
        return x.strftime("%a %d %b").replace(" 0", " ")
    except (TypeError, ValueError):
        return ""


def seg_line(s):
    kind = TYPE_WORD.get(s["type"], "Booking")
    when = fmt_date(s.get("date"))
    t = s.get("start_time") or ""
    ident = " ".join(x for x in [s.get("carrier"), s.get("number")] if x)
    if s["type"] == "hotel":
        line = f"🏨 {s['destination'] or 'Hotel'}: check-in {when} {t}".rstrip()
        if s.get("end_date"):
            line += f", check-out {fmt_date(s['end_date'])}"
    else:
        icon = {"flight": "✈️", "train": "🚆", "bus": "🚌", "cab": "🚕"}.get(s["type"], "•")
        line = f"{icon} {kind} {s['origin']} → {s['destination']}, {when} {t}".rstrip(" ,")
        if ident:
            line += f" ({ident})"
    st = s.get("status_label") or STATUS_WORD.get(s["status"], "")
    if st:
        line += f" · {st}"
    if s.get("reference"):
        line += f" · Ref {s['reference']}"
    if s.get("details"):
        line += f"\n   {s['details']}"
    return line


def compose(trip, kind, segment=None, traveler_name=""):
    words = [w for w in re.split(r"[\s.]+", traveler_name or "") if w and w.lower() not in HONORIFICS]
    first = words[0].title() if words else "there"
    segs = [s for s in trip["segments"] if s["status"] != "cancelled"] or trip["segments"]
    sign = "\n\n— Stark Travel Desk"
    if kind == "new_trip":
        return f"Hi {first}, your travel booking is in our system:\n\n" + "\n".join(seg_line(s) for s in segs) + sign
    if kind == "status" and segment:
        word = STATUS_WORD.get(segment["status"], segment["status"])
        extra = {"delayed": " We'll keep you posted on the new timing.",
                 "cancelled": " Reply here if this is unexpected and we'll help rebook.",
                 "waitlisted": " We'll update you when it confirms.",
                 "completed": ""}.get(segment["status"], "")
        return f"Hi {first}, update on your trip: {TYPE_WORD[segment['type']].lower()} is now *{word}*.\n\n{seg_line(segment)}{extra}" + sign
    if kind == "reminder" and segment:
        lead = "check-in" if segment["type"] == "hotel" else "departure"
        return f"Hi {first}, reminder of your upcoming {lead}:\n\n{seg_line(segment)}\n\nHave a safe trip!" + sign
    # manual summary
    return f"Hi {first}, here are your trip details:\n\n" + "\n".join(seg_line(s) for s in segs) + sign


def phone_digits(p):
    d = re.sub(r"\D", "", p or "")
    if len(d) == 10:          # Indian mobile without country code
        d = "91" + d
    return d


GRAPH = os.environ.get("STARK_GRAPH_URL", "https://graph.facebook.com")


def wa_ready():
    return bool(db.get_setting("wa_token", "") and db.get_setting("wa_phone_number_id", ""))


def wa_send_raw(to, body):
    """Send one message through the WhatsApp Cloud API. Returns the WhatsApp message id."""
    token = db.get_setting("wa_token", "")
    phone_id = str(db.get_setting("wa_phone_number_id", "") or "").strip()
    if not token or not phone_id:
        raise RuntimeError("WhatsApp sending is not set up. Add the access token and phone number ID in Settings.")
    to = re.sub(r"\D", "", to or "")
    if not 11 <= len(to) <= 15:
        raise RuntimeError("The WhatsApp number must include the country code.")
    template = (db.get_setting("wa_template_name", "") or "").strip()
    if template:
        # Template variables may not contain newlines, tabs or runs of 4+ spaces.
        param = re.sub(r"\s{2,}", " ", re.sub(r"\s*\n+\s*", " · ", body)).strip()[:1000]
        payload = {"messaging_product": "whatsapp", "to": to, "type": "template",
                   "template": {"name": template, "language": {"code": db.get_setting("wa_template_lang", "") or "en"},
                                "components": [{"type": "body", "parameters": [{"type": "text", "text": param}]}]}}
    else:
        payload = {"messaging_product": "whatsapp", "to": to, "type": "text",
                   "text": {"preview_url": False, "body": body[:4096]}}
    version = db.get_setting("wa_api_version", "") or "v21.0"
    req = urllib.request.Request(f"{GRAPH}/{version}/{urllib.parse.quote(phone_id)}/messages",
                                 data=json.dumps(payload).encode(), method="POST",
                                 headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            res = json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        try:
            err = json.loads(e.read() or b"{}").get("error", {}) or {}
        except ValueError:
            err = {}
        msg = (err.get("error_data") or {}).get("details") or err.get("message") or f"WhatsApp API returned {e.code}"
        if err.get("code") == 131047:
            msg += " Add an approved template name in Settings to message travellers first."
        elif err.get("code") == 190 or e.code == 401:
            msg = "WhatsApp rejected the access token. Paste a new permanent token in Settings."
        raise RuntimeError(f"WhatsApp send failed: {msg}"[:400])
    except urllib.error.URLError as e:
        raise RuntimeError(f"Could not reach WhatsApp: {e.reason}")
    return ((res.get("messages") or [{}])[0]).get("id", "")


def dispatch(trip, kind, actor, segment=None, body=None, only=None):
    """Send to every traveller on the trip with a WhatsApp number. Returns list of results."""
    results = []
    targets = trip["travelers"] or [{"name": "", "phone": "", "traveler_id": None}]
    directory = {t["id"]: t for t in db.rows("SELECT * FROM travelers")}
    for t in targets:
        if only and t["name"] not in only:
            continue
        entry = directory.get(t.get("traveler_id"))
        name = (entry or {}).get("name") or t["name"] or "Traveller"
        text = body or compose(trip, kind, segment, name)
        rec = {"trip_id": trip["id"], "segment_id": segment["id"] if segment else None, "traveler": name,
               "to_phone": "", "body": text, "trigger": kind, "provider_id": "", "error": ""}
        if not entry or not entry.get("phone"):
            rec.update(state="skipped", error=f"No WhatsApp number saved for {name}.")
        elif not entry.get("notify") and kind != "manual":
            rec.update(state="skipped", error=f"{name} has automatic updates turned off.", to_phone=entry["phone"])
        elif not wa_ready():
            # Click-to-chat mode: queue it on the dashboard's "Needs sending" list.
            rec.update(state="pending", to_phone=entry["phone"])
        else:
            rec["to_phone"] = entry["phone"]
            try:
                rec["provider_id"] = wa_send_raw(phone_digits(entry["phone"]), text)
                rec["state"] = "sent"
            except RuntimeError as e:
                rec.update(state="failed", error=str(e))
        with db.tx() as c:
            if rec["state"] == "pending":
                # A newer update replaces an unsent older one for the same person and leg.
                c.execute("UPDATE wa_messages SET state='dismissed', error='Replaced by a newer update' WHERE state='pending' "
                          "AND trip_id=? AND traveler=? AND COALESCE(segment_id,'')=COALESCE(?,'') AND trigger IN (?, 'new_trip')",
                          (rec["trip_id"], rec["traveler"], rec["segment_id"], kind))
            c.execute("INSERT INTO wa_messages(trip_id, segment_id, traveler, to_phone, body, trigger, state, provider_id, error, at) "
                      "VALUES(?,?,?,?,?,?,?,?,?,?)", (rec["trip_id"], rec["segment_id"], rec["traveler"], rec["to_phone"], rec["body"],
                                                      rec["trigger"], rec["state"], rec["provider_id"], rec["error"], db.now()))
            label = WA_LABEL.get(kind, kind)
            msg = {"sent": f"WhatsApp {label} sent to {name}", "failed": f"WhatsApp {label} to {name} failed: {rec['error']}",
                   "skipped": f"WhatsApp {label} not sent: {rec['error']}",
                   "pending": f"WhatsApp {label} for {name} is ready to send"}[rec["state"]]
            db.add_log(trip["id"], actor, "whatsapp", msg, c)
        results.append(rec)
    return results


WA_LABEL = {"new_trip": "booking confirmation", "status": "status update", "reminder": "departure reminder",
            "manual": "trip details"}


def wa_mark(mid, state, actor):
    """Click-to-chat: an admin opened a queued message in WhatsApp (state 'opened') or skipped it ('dismissed')."""
    with db.tx() as c:
        r = c.execute("SELECT * FROM wa_messages WHERE id=?", (mid,)).fetchone()
        if not r:
            raise KeyError(mid)
        if r["state"] != "pending":
            return dict(r)
        c.execute("UPDATE wa_messages SET state=?, at=? , error=? WHERE id=?",
                  (state, db.now(), "" if state == "opened" else f"Skipped by {actor}", mid))
        label = WA_LABEL.get(r["trigger"], r["trigger"])
        if r["trip_id"]:
            db.add_log(r["trip_id"], actor, "whatsapp",
                       f"Opened WhatsApp {label} for {r['traveler']}" if state == "opened" else f"Skipped WhatsApp {label} for {r['traveler']}", c)
        return dict(c.execute("SELECT * FROM wa_messages WHERE id=?", (mid,)).fetchone())


def wa_log_opened(trip, traveler, body, actor):
    """Manual 'Send to WhatsApp' in click-to-chat mode: record that the admin opened the chat."""
    entry = next((p for p in trip["travelers"] if p["name"] == traveler), None)
    if not entry or not entry.get("phone"):
        raise ValueError(f"No WhatsApp number saved for {traveler}.")
    with db.tx() as c:
        c.execute("INSERT INTO wa_messages(trip_id, segment_id, traveler, to_phone, body, trigger, state, provider_id, error, at) "
                  "VALUES(?,?,?,?,?,?,?,?,?,?)", (trip["id"], None, traveler, entry["phone"], body[:3500], "manual", "opened", "", "", db.now()))
        db.add_log(trip["id"], actor, "whatsapp", f"Opened WhatsApp trip details for {traveler}", c)


def auto_enabled(key):
    defaults = {"auto_new_trip": True, "auto_status": True}
    return bool(db.get_setting(key, defaults.get(key, False)))


def after_change(trip_id, changed_segment_ids, actor):
    if not changed_segment_ids or not auto_enabled("auto_status"):
        return
    trip = load_trip(trip_id)
    for s in trip["segments"]:
        if s["id"] in changed_segment_ids:
            dispatch(trip, "status", actor, segment=s)


def run_reminders():
    hours = float(db.get_setting("reminder_hours", 3) or 0)
    if hours <= 0:
        return
    now = datetime.now(TZ)
    sent = {r["segment_id"] for r in db.rows("SELECT DISTINCT segment_id FROM wa_messages WHERE trigger='reminder' AND segment_id IS NOT NULL")}
    for t in list_trips():
        if t["phase"] in ("completed", "cancelled"):
            continue
        for s in t["segments"]:
            if s["id"] in sent or s["status"] in ("cancelled", "completed"):
                continue
            st = seg_start(s)
            if st and s.get("start_time") and now < st <= now + timedelta(hours=hours):
                dispatch(t, "reminder", "Stark Travel Desk", segment=s)


# ---------------------------------------------------------------- Gmail sync

def find_group(names, segs):
    """An open trip for the same travellers within 3 days of these segments."""
    dates = [date.fromisoformat(s["date"]) for s in segs if s.get("date")]
    if not dates or not names:
        return None
    lo, hi = min(dates) - timedelta(days=3), max(dates) + timedelta(days=3)
    directory = db.rows("SELECT * FROM travelers")
    for t in list_trips():
        if t["phase"] == "cancelled":
            continue
        if not any(same_person(n, x["name"], directory) for n in names for x in t["travelers"]):
            continue
        tdates = [date.fromisoformat(s["date"]) for s in t["segments"] if s.get("date")]
        if tdates and min(tdates) <= hi and max(tdates) >= lo:
            return t
    return None


def seg_key(s):
    return (s["type"], (s.get("reference") or "").upper(), (s.get("number") or "").upper(), s.get("date") or "",
            (s.get("origin") or "").upper()[:20], (s.get("destination") or "").upper()[:20])


def ingest(parsed, email_id, actor="Stark Decoder"):
    """Apply a decoded email. Returns (trip_id, created, status_changes)."""
    segs = [clean_seg(s) for s in parsed.get("segments", [])]
    names = [n for n in parsed.get("travelers", []) if n.strip()]
    if not segs:
        return None, False, []
    # same booking seen before (PNR/number/date) -> update in place
    for t in list_trips():
        existing = {seg_key(s): s for s in t["segments"]}
        if any(seg_key(s) in existing for s in segs) or any(
                s.get("reference") and any(x.get("reference", "").upper() == s["reference"].upper() and x["type"] == s["type"]
                                           for x in t["segments"]) for s in segs):
            merged = [dict(x) for x in t["segments"]]
            for s in segs:
                hit = next((m for m in merged if seg_key(m) == seg_key(s) or
                            (s.get("reference") and m.get("reference", "").upper() == s["reference"].upper() and m["type"] == s["type"]
                             and (m.get("date") == s.get("date") or not s.get("date")))), None)
                if hit:
                    for k in SEG_FIELDS:
                        if s.get(k):
                            hit[k] = s[k]
                else:
                    merged.append(dict(s, id=None))
            tnames = [x["name"] for x in t["travelers"]]
            tnames += [n for n in names if not any(same_person(n, x) for x in tnames)]
            tid, changes = save_trip(t["id"], {"title": t["title"], "travelers": tnames, "cancelled": t["cancelled"],
                                               "notes": t["notes"], "segments": merged, "email_id": email_id}, actor)
            return tid, False, changes
    group = find_group(names, segs)
    if group:
        merged = [dict(x) for x in group["segments"]] + [dict(s, id=None) for s in segs]
        merged.sort(key=lambda s: ((s.get("date") or "9999"), (s.get("start_time") or "")))
        tnames = [x["name"] for x in group["travelers"]]
        tnames += [n for n in names if not any(same_person(n, x) for x in tnames)]
        save_trip(group["id"], {"title": group["title"], "travelers": tnames, "cancelled": group["cancelled"], "notes": group["notes"],
                                "segments": merged, "email_id": email_id}, actor)
        return group["id"], True, []
    tid, _ = save_trip(None, {"title": parsed.get("trip_title") or "Booking", "travelers": names, "segments": segs,
                              "source": "gmail", "email_id": email_id, "log_added": False}, actor)
    return tid, True, []


def sync_gmail(force_ids=None):
    """Pull new booking emails, decode them, create/update trips, and send automatic WhatsApp updates."""
    import decoder
    if not sync_lock.acquire(blocking=False):
        return {"busy": True}
    summary = {"checked": 0, "parsed": 0, "ignored": 0, "errors": 0, "trips": []}
    try:
        g = gmail.Gmail(db.get_setting("gmail_client_id", ""), db.get_setting("gmail_client_secret", ""),
                        db.get_setting("gmail_refresh_token", ""))
        query = db.get_setting("gmail_query", "") or gmail.DEFAULT_QUERY
        ids = force_ids or g.search(query, limit=int(db.get_setting("gmail_max", 40) or 40))
        done = {r["gmail_id"]: r["state"] for r in db.rows("SELECT gmail_id, state FROM emails")}
        api_key = db.get_setting("deepseek_api_key", "")
        model = db.get_setting("deepseek_model", "") or None
        for mid in ids:
            if not force_ids and done.get(mid) in ("parsed", "ignored"):
                continue
            summary["checked"] += 1
            subject = sender = ""
            received = None
            try:
                msg = g.message(mid)
                headers, text, pdf_refs = gmail.extract(g, msg)
                subject, sender = headers.get("subject", "")[:300], headers.get("from", "")[:200]
                try:
                    received = parsedate_to_datetime(headers.get("date")).timestamp()
                except (TypeError, ValueError):
                    received = int(msg.get("internalDate", 0)) / 1000 or None
                pdfs = gmail.fetch_pdfs(g, mid, pdf_refs)
                rec_str = datetime.fromtimestamp(received, TZ).isoformat() if received else ""
                parsed = decoder.decode(api_key, subject, sender, rec_str, text, pdfs, model)
                if not parsed.get("is_travel_booking") or not parsed.get("segments"):
                    state, trip_id, err = "ignored", None, ""
                    summary["ignored"] += 1
                else:
                    trip_id, created, changes = ingest(parsed, mid)
                    db.add_log(trip_id, "Stark Decoder", "email", f"Read email “{subject}” from {sender}")
                    state, err = "parsed", ""
                    summary["parsed"] += 1
                    summary["trips"].append(trip_id)
                    if created and auto_enabled("auto_new_trip"):
                        dispatch(load_trip(trip_id), "new_trip", "Stark Travel Desk")
                    after_change(trip_id, changes, "Stark Travel Desk")
            except (decoder.DecoderError, gmail.GmailError, ValueError, KeyError) as e:
                state, trip_id, err = "error", None, str(e)[:500]
                summary["errors"] += 1
            with db.tx() as c:
                c.execute("INSERT INTO emails(gmail_id, subject, sender, received_at, state, trip_id, error, processed_at) "
                          "VALUES(?,?,?,?,?,?,?,?) ON CONFLICT(gmail_id) DO UPDATE SET subject=excluded.subject, "
                          "sender=excluded.sender, received_at=excluded.received_at, state=excluded.state, "
                          "trip_id=excluded.trip_id, error=excluded.error, processed_at=excluded.processed_at",
                          (mid, subject, sender, received, state, trip_id, err, db.now()))
        db.set_setting("gmail_last_sync", {"at": db.now(), "ok": True, **{k: summary[k] for k in ("checked", "parsed", "ignored", "errors")}})
    except gmail.GmailError as e:
        db.set_setting("gmail_last_sync", {"at": db.now(), "ok": False, "error": str(e)[:300]})
        summary["error"] = str(e)
    finally:
        sync_lock.release()
    return summary


def background_loop(stop):
    while not stop.is_set():
        try:
            if db.get_setting("gmail_refresh_token", ""):
                last = db.get_setting("gmail_last_sync", {}) or {}
                every = max(5, int(db.get_setting("sync_minutes", 10) or 10)) * 60
                if time.time() - last.get("at", 0) >= every:
                    sync_gmail()
            run_reminders()
        except Exception as e:  # keep the loop alive; surface in Settings
            db.set_setting("background_error", {"at": db.now(), "error": repr(e)[:300]})
        stop.wait(60)

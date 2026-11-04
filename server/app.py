#!/usr/bin/env python3
"""Stark Travel Desk API. Runs on 127.0.0.1; nginx serves web/ and proxies /api/ here.

Data lives in SQLite under STARK_DATA_DIR. Sign-in uses users created from the
server (PBKDF2 hashes) and an HttpOnly session cookie.

Manage users (run as the service user):
    python3 app.py add-user NAME | passwd NAME | del-user NAME | list-users
"""
import getpass
import hashlib
import hmac
import json
import os
import re
import secrets
import sys
import threading
import time
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import core  # noqa: E402
import db  # noqa: E402
import gmail  # noqa: E402

PORT = int(os.environ.get("STARK_PORT", "8795"))
BASE_URL = os.environ.get("STARK_BASE_URL", "https://travel.starkpeople.in").rstrip("/")
COOKIE = "std_session"
SESSION_DAYS = 14
MAX_BODY = 2 * 1024 * 1024

SECRET_KEYS = {"gmail_client_secret", "gmail_refresh_token", "anthropic_api_key", "wa_function_secret"}
SETTING_KEYS = {"gmail_client_id", "gmail_client_secret", "gmail_query", "gmail_max", "sync_minutes",
                "anthropic_api_key", "wa_function_url", "wa_function_secret",
                "auto_new_trip", "auto_status", "reminder_hours"}


# ---------------------------------------------------------------- passwords & sessions

def hash_pw(pw, salt=None, n=310_000):
    salt = salt or secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", pw.encode(), bytes.fromhex(salt), n)
    return f"pbkdf2${n}${salt}${dk.hex()}"


def check_pw(pw, stored):
    try:
        _, n, salt, h = stored.split("$")
        return hmac.compare_digest(hash_pw(pw, salt, int(n)).split("$")[3], h)
    except ValueError:
        return False


def tok_hash(t):
    return hashlib.sha256(t.encode()).hexdigest()


_login_fail = {}


class Handler(BaseHTTPRequestHandler):
    server_version = "StarkTravelDesk/1.0"

    def log_message(self, fmt, *args):
        if os.environ.get("STARK_DEBUG"):
            super().log_message(fmt, *args)

    # ---- plumbing
    def send_json(self, code, obj, headers=None):
        body = json.dumps(obj, default=str).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def redirect(self, loc):
        self.send_response(302)
        self.send_header("Location", loc)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def body(self):
        n = int(self.headers.get("Content-Length") or 0)
        if n > MAX_BODY:
            raise ValueError("Request too large.")
        raw = self.rfile.read(n) if n else b"{}"
        return json.loads(raw or b"{}")

    def cookie(self):
        for part in (self.headers.get("Cookie") or "").split(";"):
            k, _, v = part.strip().partition("=")
            if k == COOKIE:
                return v
        return None

    def user(self):
        t = self.cookie()
        if not t:
            return None
        r = db.one("SELECT username, expires_at FROM sessions WHERE token_hash = ?", (tok_hash(t),))
        if not r or r["expires_at"] < time.time():
            return None
        return r["username"]

    def client_ip(self):
        return self.headers.get("X-Real-IP") or self.client_address[0]

    def same_origin(self):
        # CSRF guard for state-changing requests: browsers send Origin on POST/PUT/DELETE.
        o = self.headers.get("Origin")
        if not o:
            return True
        host = self.headers.get("X-Forwarded-Host") or self.headers.get("Host") or ""
        return urllib.parse.urlparse(o).netloc == host

    # ---- routing
    def do_GET(self):
        self.route("GET")

    def do_POST(self):
        self.route("POST")

    def do_PUT(self):
        self.route("PUT")

    def do_DELETE(self):
        self.route("DELETE")

    def route(self, method):
        u = urllib.parse.urlparse(self.path)
        path = u.path.rstrip("/") or "/"
        if path.startswith("/api"):
            path = path[4:] or "/"
        q = dict(urllib.parse.parse_qsl(u.query))
        try:
            if path == "/health":
                return self.send_json(200, {"ok": True})
            if path == "/login" and method == "POST":
                return self.login()
            if method != "GET" and not self.same_origin():
                return self.send_json(403, {"error": "Cross-site request refused."})
            user = self.user()
            if not user:
                if path == "/gmail/callback":
                    return self.redirect("/?gmail=signin")
                return self.send_json(401, {"error": "Please sign in."})
            handler = ROUTES.get((method, re.sub(r"/[0-9a-f]{12}(?=/|$)", "/:id", path)))
            if not handler:
                return self.send_json(404, {"error": "Not found."})
            ids = re.findall(r"/([0-9a-f]{12})(?=/|$)", path)
            return handler(self, user, q, *ids)
        except KeyError:
            return self.send_json(404, {"error": "That trip no longer exists."})
        except (ValueError, json.JSONDecodeError) as e:
            return self.send_json(400, {"error": str(e) or "Invalid request."})
        except Exception as e:  # noqa: BLE001
            sys.stderr.write(f"error on {method} {self.path}: {e!r}\n")
            return self.send_json(500, {"error": "Something went wrong on the server. Check the service log."})

    # ---- auth
    def login(self):
        ip = self.client_ip()
        fails = [t for t in _login_fail.get(ip, []) if t > time.time() - 900]
        if len(fails) >= 8:
            return self.send_json(429, {"error": "Too many attempts. Wait 15 minutes and try again."})
        b = self.body()
        u = db.one("SELECT * FROM users WHERE username = ?", (str(b.get("username", "")).strip(),))
        if not u or not check_pw(str(b.get("password", "")), u["pwhash"]):
            _login_fail[ip] = fails + [time.time()]
            return self.send_json(401, {"error": "Wrong username or password."})
        _login_fail.pop(ip, None)
        t = secrets.token_urlsafe(32)
        days = SESSION_DAYS if b.get("remember", True) else 1
        with db.tx() as c:
            c.execute("DELETE FROM sessions WHERE expires_at < ?", (time.time(),))
            c.execute("INSERT INTO sessions VALUES(?,?,?)", (tok_hash(t), u["username"], time.time() + days * 86400))
        secure = "; Secure" if BASE_URL.startswith("https") else ""
        return self.send_json(200, {"user": u["username"]}, {
            "Set-Cookie": f"{COOKIE}={t}; Path=/; HttpOnly; SameSite=Lax; Max-Age={days * 86400}{secure}"})


# ---------------------------------------------------------------- route handlers

def r_me(h, user, q):
    return h.send_json(200, {"user": user})


def r_logout(h, user, q):
    t = h.cookie()
    with db.tx() as c:
        c.execute("DELETE FROM sessions WHERE token_hash = ?", (tok_hash(t),))
    return h.send_json(200, {}, {"Set-Cookie": f"{COOKIE}=; Path=/; HttpOnly; SameSite=Lax; Max-Age=0"})


def r_password(h, user, q):
    b = h.body()
    u = db.one("SELECT * FROM users WHERE username = ?", (user,))
    if not check_pw(str(b.get("current", "")), u["pwhash"]):
        return h.send_json(400, {"error": "Current password is wrong."})
    new = str(b.get("new", ""))
    if len(new) < 10:
        return h.send_json(400, {"error": "Use at least 10 characters."})
    with db.tx() as c:
        c.execute("UPDATE users SET pwhash = ? WHERE username = ?", (hash_pw(new), user))
    return h.send_json(200, {})


def r_trips(h, user, q):
    return h.send_json(200, {"trips": core.list_trips(), "status": status_info()})


def r_trip_create(h, user, q):
    tid, _ = core.save_trip(None, h.body(), user)
    return h.send_json(200, {"trip": core.load_trip(tid)})


def r_trip_update(h, user, q, tid):
    b = h.body()
    _, changes = core.save_trip(tid, b, user)
    if b.get("notify", True):
        core.after_change(tid, changes, user)
    return h.send_json(200, {"trip": core.load_trip(tid)})


def r_trip_delete(h, user, q, tid):
    core.delete_trip(tid)
    return h.send_json(200, {})


def r_trip_merge(h, user, q, tid):
    into = str(h.body().get("into", ""))
    core.merge_trips(tid, into, user)
    return h.send_json(200, {"trip": core.load_trip(into)})


def r_trip_log(h, user, q, tid):
    log = db.rows("SELECT at, actor, kind, message FROM log WHERE trip_id = ? ORDER BY id DESC LIMIT 200", (tid,))
    wa = db.rows("SELECT id, at, traveler, to_phone, body, trigger, state, error FROM wa_messages WHERE trip_id = ? ORDER BY id DESC LIMIT 50", (tid,))
    emails = db.rows("SELECT gmail_id, subject, sender, received_at FROM emails WHERE trip_id = ? ORDER BY received_at DESC", (tid,))
    return h.send_json(200, {"log": log, "whatsapp": wa, "emails": emails})


def r_trip_preview(h, user, q, tid):
    trip = core.load_trip(tid)
    if not trip:
        raise KeyError(tid)
    first = trip["travelers"][0]["name"] if trip["travelers"] else ""
    return h.send_json(200, {"body": core.compose(trip, "manual", None, first), "travelers": trip["travelers"]})


def r_trip_whatsapp(h, user, q, tid):
    b = h.body()
    trip = core.load_trip(tid)
    if not trip:
        raise KeyError(tid)
    body = str(b.get("body") or "").strip()[:3500] or None
    only = b.get("travelers") or None
    res = core.dispatch(trip, "manual", user, body=body, only=only)
    return h.send_json(200, {"results": [{k: r[k] for k in ("traveler", "state", "error", "to_phone")} for r in res]})


def r_travelers(h, user, q):
    return h.send_json(200, {"travelers": db.rows("SELECT * FROM travelers ORDER BY name COLLATE NOCASE")})


def _traveler_fields(b):
    name = str(b.get("name", "")).strip()[:120]
    if not name:
        raise ValueError("Enter the traveller's name.")
    phone = str(b.get("phone", "")).strip()[:30]
    if phone and len(re.sub(r"\D", "", phone)) < 10:
        raise ValueError("Enter the WhatsApp number with country code, e.g. +91 98765 43210.")
    return (name, phone, str(b.get("email", "")).strip()[:200], str(b.get("aliases", "")).strip()[:500], int(bool(b.get("notify", True))))


def r_traveler_create(h, user, q):
    f = _traveler_fields(h.body())
    tid = db.new_id()
    with db.tx() as c:
        c.execute("INSERT INTO travelers(id, name, phone, email, aliases, notify, created_at) VALUES(?,?,?,?,?,?,?)", (tid,) + f + (db.now(),))
    return h.send_json(200, {"traveler": db.one("SELECT * FROM travelers WHERE id = ?", (tid,))})


def r_traveler_update(h, user, q, tid):
    f = _traveler_fields(h.body())
    with db.tx() as c:
        c.execute("UPDATE travelers SET name=?, phone=?, email=?, aliases=?, notify=? WHERE id=?", f + (tid,))
    return h.send_json(200, {"traveler": db.one("SELECT * FROM travelers WHERE id = ?", (tid,))})


def r_traveler_delete(h, user, q, tid):
    with db.tx() as c:
        c.execute("DELETE FROM travelers WHERE id = ?", (tid,))
    return h.send_json(200, {})


def status_info():
    return {
        "gmail_connected": bool(db.get_setting("gmail_refresh_token", "")),
        "gmail_account": db.get_setting("gmail_account", ""),
        "gmail_last_sync": db.get_setting("gmail_last_sync", None),
        "decoder_ready": bool(db.get_setting("anthropic_api_key", "")),
        "whatsapp_ready": bool(db.get_setting("wa_function_url", "") and db.get_setting("wa_function_secret", "")),
        "sync_minutes": db.get_setting("sync_minutes", 10),
        "background_error": db.get_setting("background_error", None),
    }


def r_settings(h, user, q):
    out = {}
    for k in SETTING_KEYS:
        v = db.get_setting(k, None)
        out[k] = ("set" if v else "") if k in SECRET_KEYS else v
    out.setdefault("gmail_query", "")
    out["default_gmail_query"] = gmail.DEFAULT_QUERY
    out["gmail_redirect_uri"] = BASE_URL + "/api/gmail/callback"
    out["status"] = status_info()
    return h.send_json(200, out)


def r_settings_save(h, user, q):
    b = h.body()
    for k, v in b.items():
        if k not in SETTING_KEYS:
            continue
        if k in SECRET_KEYS and (v is None or v == "" or v == "set"):
            continue  # unchanged
        if k in ("gmail_max", "sync_minutes"):
            v = max(1, min(200, int(v or 0)))
        if k == "reminder_hours":
            v = max(0.0, min(48.0, float(v or 0)))
        if k in ("auto_new_trip", "auto_status"):
            v = bool(v)
        if k == "wa_function_url" and v and not str(v).startswith("https://"):
            raise ValueError("The WhatsApp function URL must start with https://")
        db.set_setting(k, v)
    if b.get("clear_gmail"):
        for k in ("gmail_refresh_token", "gmail_account"):
            db.set_setting(k, None)
    return r_settings(h, user, q)


def r_gmail_connect(h, user, q):
    cid = db.get_setting("gmail_client_id", "")
    if not cid or not db.get_setting("gmail_client_secret", ""):
        return h.redirect("/?gmail=missing-client")
    state = secrets.token_urlsafe(24)
    db.set_setting("gmail_oauth_state", {"state": state, "at": time.time(), "user": user})
    return h.redirect(gmail.auth_url(cid, BASE_URL + "/api/gmail/callback", state))


def r_gmail_callback(h, user, q):
    st = db.get_setting("gmail_oauth_state", {}) or {}
    if not q.get("state") or q.get("state") != st.get("state") or time.time() - st.get("at", 0) > 900:
        return h.redirect("/?gmail=expired")
    db.set_setting("gmail_oauth_state", None)
    if q.get("error"):
        return h.redirect("/?gmail=denied")
    try:
        tok = gmail.exchange_code(db.get_setting("gmail_client_id", ""), db.get_setting("gmail_client_secret", ""),
                                  BASE_URL + "/api/gmail/callback", q.get("code", ""))
        if not tok.get("refresh_token"):
            return h.redirect("/?gmail=no-refresh")
        db.set_setting("gmail_refresh_token", tok["refresh_token"])
        prof = gmail.Gmail(db.get_setting("gmail_client_id", ""), db.get_setting("gmail_client_secret", ""), tok["refresh_token"]).profile()
        db.set_setting("gmail_account", prof.get("emailAddress", ""))
    except gmail.GmailError:
        return h.redirect("/?gmail=failed")
    threading.Thread(target=core.sync_gmail, daemon=True).start()
    return h.redirect("/?gmail=connected")


def r_gmail_sync(h, user, q):
    res = core.sync_gmail()
    if res.get("busy"):
        return h.send_json(409, {"error": "A sync is already running. Try again in a minute."})
    if res.get("error"):
        return h.send_json(400, {"error": res["error"]})
    return h.send_json(200, res)


def r_emails(h, user, q):
    return h.send_json(200, {"emails": db.rows("SELECT * FROM emails ORDER BY processed_at DESC LIMIT 100")})


def r_email_retry(h, user, q):
    gid = str(h.body().get("gmail_id", ""))
    if not re.fullmatch(r"[0-9a-zA-Z]{6,40}", gid):
        raise ValueError("Unknown email.")
    res = core.sync_gmail(force_ids=[gid])
    if res.get("busy"):
        return h.send_json(409, {"error": "A sync is already running. Try again in a minute."})
    if res.get("error"):
        return h.send_json(400, {"error": res["error"]})
    return h.send_json(200, res)


def r_wa_test(h, user, q):
    to = core.phone_digits(str(h.body().get("to", "")))
    if len(to) < 11:
        raise ValueError("Enter a WhatsApp number with country code.")
    try:
        pid = core.wa_send_raw(to, "Test message from Stark Travel Desk. WhatsApp updates are working.")
    except RuntimeError as e:
        return h.send_json(400, {"error": str(e)})
    with db.tx() as c:
        c.execute("INSERT INTO wa_messages(trip_id, traveler, to_phone, body, trigger, state, provider_id, at) VALUES(NULL,?,?,?,?,?,?,?)",
                  (user, to, "Test message", "test", "sent", pid, db.now()))
    return h.send_json(200, {"ok": True})


def r_wa_messages(h, user, q):
    return h.send_json(200, {"messages": db.rows(
        "SELECT w.*, t.title FROM wa_messages w LEFT JOIN trips t ON t.id = w.trip_id ORDER BY w.id DESC LIMIT 150")})


ROUTES = {
    ("GET", "/me"): r_me,
    ("POST", "/logout"): r_logout,
    ("POST", "/password"): r_password,
    ("GET", "/trips"): r_trips,
    ("POST", "/trips"): r_trip_create,
    ("PUT", "/trips/:id"): r_trip_update,
    ("DELETE", "/trips/:id"): r_trip_delete,
    ("POST", "/trips/:id/merge"): r_trip_merge,
    ("GET", "/trips/:id/log"): r_trip_log,
    ("GET", "/trips/:id/whatsapp"): r_trip_preview,
    ("POST", "/trips/:id/whatsapp"): r_trip_whatsapp,
    ("GET", "/travelers"): r_travelers,
    ("POST", "/travelers"): r_traveler_create,
    ("PUT", "/travelers/:id"): r_traveler_update,
    ("DELETE", "/travelers/:id"): r_traveler_delete,
    ("GET", "/settings"): r_settings,
    ("PUT", "/settings"): r_settings_save,
    ("GET", "/gmail/connect"): r_gmail_connect,
    ("GET", "/gmail/callback"): r_gmail_callback,
    ("POST", "/gmail/sync"): r_gmail_sync,
    ("GET", "/emails"): r_emails,
    ("POST", "/emails/retry"): r_email_retry,
    ("POST", "/whatsapp/test"): r_wa_test,
    ("GET", "/whatsapp/messages"): r_wa_messages,
}


# ---------------------------------------------------------------- CLI

def cli(args):
    cmd = args[0]
    if cmd in ("add-user", "passwd"):
        name = args[1]
        pw = os.environ.get("STARK_PASSWORD") or getpass.getpass(f"Password for {name} (min 10 chars): ")
        if len(pw) < 10:
            sys.exit("Password must be at least 10 characters.")
        with db.tx() as c:
            c.execute("INSERT INTO users(username, pwhash, created_at) VALUES(?,?,?) ON CONFLICT(username) DO UPDATE SET pwhash=excluded.pwhash",
                      (name, hash_pw(pw), time.time()))
        print(name)
    elif cmd == "del-user":
        with db.tx() as c:
            c.execute("DELETE FROM users WHERE username = ?", (args[1],))
            c.execute("DELETE FROM sessions WHERE username = ?", (args[1],))
    elif cmd == "list-users":
        for r in db.rows("SELECT username FROM users ORDER BY username"):
            print(r["username"])
    else:
        sys.exit(__doc__)


def main():
    if len(sys.argv) > 1:
        return cli(sys.argv[1:])
    db.con()
    stop = threading.Event()
    threading.Thread(target=core.background_loop, args=(stop,), daemon=True).start()
    srv = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"Stark Travel Desk API on 127.0.0.1:{PORT}", flush=True)
    try:
        srv.serve_forever()
    finally:
        stop.set()


if __name__ == "__main__":
    main()

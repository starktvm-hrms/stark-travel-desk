"""Stark Decoder: turns a booking email (text + PDF tickets) into trip segments with DeepSeek."""
import io
import json
import os
import urllib.error
import urllib.request

API_URL = os.environ.get("STARK_DEEPSEEK_URL", "https://api.deepseek.com/chat/completions")
DEFAULT_MODEL = "deepseek-chat"

SEGMENT_TYPES = ["flight", "train", "bus", "cab", "hotel", "other"]
STATUSES = ["reserved", "confirmed", "waitlisted", "delayed", "completed", "cancelled"]

SYSTEM = """You read booking emails for a corporate travel desk in India and extract the itinerary as JSON.
Report only what the email states; never invent dates, times, numbers or names.
Use one segment per leg: each flight or train leg, each cab ride, each hotel stay.
Dates may be written like 20-Aug-2026 or 5/28/2026; convert them to YYYY-MM-DD. Times become 24-hour HH:MM.
Indian railway station codes (LTT, KYJ, ERS) and IATA codes go in brackets after the city name when both are given.

Reply with one JSON object exactly in this shape:
{
  "is_travel_booking": true,          // false for marketing, OTPs, newsletters, anything that is not a real booking, change or cancellation
  "trip_title": "IRCTC Train 16345, LTT - KYJ, 20 Aug",
  "travelers": ["Passenger names exactly as printed"],
  "segments": [
    {
      "type": "flight | train | bus | cab | hotel | other",
      "status": "reserved | confirmed | waitlisted | delayed | completed | cancelled",
      "status_label": "status as written in the email, e.g. CNF, RAC 12, Confirmed",
      "origin": "departure place, e.g. Mumbai (LTT). For hotels: Hotel Stay",
      "destination": "arrival place. For hotels: the hotel name",
      "date": "YYYY-MM-DD departure / check-in date, or null",
      "start_time": "HH:MM departure / check-in time, or null",
      "end_date": "YYYY-MM-DD arrival / check-out date, or null",
      "end_time": "HH:MM arrival / check-out time, or null",
      "carrier": "airline, train name, cab company or hotel chain, or empty string",
      "number": "flight number, train number or vehicle registration, or empty string",
      "reference": "PNR / booking ID / confirmation number, or empty string",
      "details": "one line: coach, berth, class, seat, vehicle model, room type; or empty string"
    }
  ]
}
Status rules: CNF/Booked -> confirmed; RAC/WL -> waitlisted; hotel reservations -> reserved; finished rides and receipts -> completed.
If it is not a travel booking, return {"is_travel_booking": false, "trip_title": "", "travelers": [], "segments": []}."""


class DecoderError(Exception):
    pass


def pdf_text(data):
    """Text of a PDF ticket (IRCTC, airline e-tickets are text PDFs). Empty string if unreadable."""
    try:
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(data))
        if reader.is_encrypted:
            try:
                reader.decrypt("")
            except Exception:  # noqa: BLE001
                return ""
        return "\n".join((p.extract_text() or "") for p in reader.pages[:10]).strip()
    except Exception:  # noqa: BLE001 - a broken attachment must not stop the email
        return ""


def _normalise(obj):
    if not isinstance(obj, dict):
        raise DecoderError("DeepSeek returned something other than a JSON object.")
    segs = []
    for s in obj.get("segments") or []:
        if not isinstance(s, dict) or not (str(s.get("origin") or "").strip() or str(s.get("destination") or "").strip()):
            continue
        s = dict(s)
        s["type"] = s.get("type") if s.get("type") in SEGMENT_TYPES else "other"
        s["status"] = s.get("status") if s.get("status") in STATUSES else "confirmed"
        for k in ("date", "start_time", "end_date", "end_time"):
            if s.get(k) in ("", "null", "None"):
                s[k] = None
        segs.append(s)
    travelers = [str(n) for n in (obj.get("travelers") or []) if isinstance(n, (str, int)) and str(n).strip()]
    return {"is_travel_booking": bool(obj.get("is_travel_booking")) and bool(segs),
            "trip_title": str(obj.get("trip_title") or "")[:200], "travelers": travelers, "segments": segs}


def decode(api_key, subject, sender, received, body_text, pdfs, model=None):
    """pdfs: list of (filename, bytes). Returns the parsed dict."""
    if not api_key:
        raise DecoderError("Add a DeepSeek API key in Settings so booking emails can be read.")
    parts = [f"Subject: {subject}\nFrom: {sender}\nReceived: {received}\n\nEmail body:\n{body_text[:40000]}"]
    for name, data in pdfs[:4]:
        txt = pdf_text(data)
        if txt:
            parts.append(f"\n\nAttached PDF '{name}':\n{txt[:20000]}")
    payload = {
        "model": model or DEFAULT_MODEL,
        "messages": [{"role": "system", "content": SYSTEM},
                     {"role": "user", "content": "".join(parts) + "\n\nReturn the itinerary JSON."}],
        "response_format": {"type": "json_object"},
        "temperature": 0,
        "max_tokens": 8000,
        "stream": False,
    }
    req = urllib.request.Request(API_URL, data=json.dumps(payload).encode(), method="POST",
                                 headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"})
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            res = json.loads(r.read())
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="replace")[:200]
        msg = {401: "The DeepSeek API key was rejected. Check it in Settings.",
               402: "The DeepSeek account is out of balance. Top it up at platform.deepseek.com.",
               422: f"DeepSeek rejected the request: {detail}",
               429: "DeepSeek rate limit reached; the email will be retried on the next sync."}.get(e.code)
        if not msg and e.code == 400 and "model" in detail.lower():
            msg = "DeepSeek doesn't recognise the model name in Settings."
        raise DecoderError(msg or f"DeepSeek API error {e.code}; will retry on the next sync.")
    except (urllib.error.URLError, TimeoutError):
        raise DecoderError("Could not reach the DeepSeek API; will retry on the next sync.")

    choice = (res.get("choices") or [{}])[0]
    if choice.get("finish_reason") == "length":
        raise DecoderError("The email was too long for DeepSeek to answer in one pass.")
    text = ((choice.get("message") or {}).get("content") or "").strip()
    if not text:
        raise DecoderError("DeepSeek returned an empty answer; will retry on the next sync.")
    try:
        return _normalise(json.loads(text))
    except json.JSONDecodeError:
        raise DecoderError("DeepSeek's answer was not valid JSON; will retry on the next sync.")

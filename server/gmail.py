"""Read-only Gmail access over the Gmail REST API (OAuth 2.0, stdlib only)."""
import base64
import html
import json
import re
import urllib.error
import urllib.parse
import urllib.request

AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
API = "https://gmail.googleapis.com/gmail/v1/users/me"
SCOPE = "https://www.googleapis.com/auth/gmail.readonly"

DEFAULT_QUERY = ('newer_than:45d -category:promotions -category:social '
                 '(subject:(booking OR ticket OR "e-ticket" OR itinerary OR reservation OR PNR OR '
                 'confirmation OR trip OR ride OR receipt OR "check-in") '
                 'OR from:(irctc.co.in OR uber.com OR olacabs.com OR makemytrip.com OR goibibo.com OR '
                 'cleartrip.com OR ixigo.com OR redbus.in OR goindigo.in OR airindia.com OR akasaair.com OR '
                 'spicejet.com OR booking.com OR agoda.com OR oyorooms.com OR marriott.com OR tajhotels.com))')


class GmailError(Exception):
    pass


def _post_form(url, data):
    req = urllib.request.Request(url, data=urllib.parse.urlencode(data).encode(), method="POST",
                                 headers={"Content-Type": "application/x-www-form-urlencoded"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        try:
            err = json.loads(body)
            msg = err.get("error_description") or err.get("error") or body
        except ValueError:
            msg = body
        raise GmailError(f"Google sign-in failed: {msg}")


def auth_url(client_id, redirect_uri, state):
    return AUTH_URL + "?" + urllib.parse.urlencode({
        "client_id": client_id, "redirect_uri": redirect_uri, "response_type": "code",
        "scope": SCOPE, "access_type": "offline", "prompt": "consent", "state": state,
        "include_granted_scopes": "true",
    })


def exchange_code(client_id, client_secret, redirect_uri, code):
    return _post_form(TOKEN_URL, {"code": code, "client_id": client_id, "client_secret": client_secret,
                                  "redirect_uri": redirect_uri, "grant_type": "authorization_code"})


class Gmail:
    def __init__(self, client_id, client_secret, refresh_token):
        if not (client_id and client_secret and refresh_token):
            raise GmailError("Gmail is not connected. Open Settings and connect the travel inbox.")
        self.cid, self.secret, self.refresh = client_id, client_secret, refresh_token
        self.token = None

    def _access(self):
        if not self.token:
            r = _post_form(TOKEN_URL, {"client_id": self.cid, "client_secret": self.secret,
                                       "refresh_token": self.refresh, "grant_type": "refresh_token"})
            self.token = r["access_token"]
        return self.token

    def _get(self, path, params=None):
        url = API + path + ("?" + urllib.parse.urlencode(params, doseq=True) if params else "")
        for attempt in (0, 1):
            req = urllib.request.Request(url, headers={"Authorization": "Bearer " + self._access()})
            try:
                with urllib.request.urlopen(req, timeout=60) as r:
                    return json.loads(r.read())
            except urllib.error.HTTPError as e:
                if e.code == 401 and attempt == 0:
                    self.token = None
                    continue
                raise GmailError(f"Gmail API error {e.code}: {e.read().decode(errors='replace')[:300]}")
        raise GmailError("Gmail authorisation failed.")

    def profile(self):
        return self._get("/profile")

    def search(self, query, limit=50):
        ids, page = [], None
        while len(ids) < limit:
            params = {"q": query, "maxResults": min(100, limit - len(ids))}
            if page:
                params["pageToken"] = page
            r = self._get("/messages", params)
            ids += [m["id"] for m in r.get("messages", [])]
            page = r.get("nextPageToken")
            if not page:
                break
        return ids

    def message(self, mid):
        return self._get(f"/messages/{mid}", {"format": "full"})

    def attachment(self, mid, aid):
        r = self._get(f"/messages/{mid}/attachments/{aid}")
        return _b64(r["data"])


def _b64(s):
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def html_to_text(h):
    h = re.sub(r"(?is)<(script|style|head)[^>]*>.*?</\1>", " ", h)
    h = re.sub(r"(?i)<br\s*/?>|</(p|div|tr|li|h\d|table)>", "\n", h)
    h = re.sub(r"(?i)</t[dh]>", " | ", h)
    h = re.sub(r"<[^>]+>", " ", h)
    h = html.unescape(h)
    h = re.sub(r"[ \t\r\f\v]+", " ", h)
    return re.sub(r"\n\s*\n+", "\n", h).strip()


def extract(gm, msg):
    """Returns (headers dict, text body, [(pdf_name, attachment_id)])."""
    headers = {h["name"].lower(): h["value"] for h in msg.get("payload", {}).get("headers", [])}
    plain, htmls, pdfs = [], [], []

    def walk(part):
        mime = part.get("mimeType", "")
        body = part.get("body", {})
        name = part.get("filename") or ""
        if name.lower().endswith(".pdf") or mime == "application/pdf":
            if body.get("attachmentId") and body.get("size", 0) <= 8_000_000:
                pdfs.append((name or "ticket.pdf", body["attachmentId"]))
            elif body.get("data"):
                pdfs.append((name or "ticket.pdf", ("inline", body["data"])))
        elif mime == "text/plain" and body.get("data"):
            plain.append(_b64(body["data"]).decode(errors="replace"))
        elif mime == "text/html" and body.get("data"):
            htmls.append(_b64(body["data"]).decode(errors="replace"))
        for p in part.get("parts", []) or []:
            walk(p)

    walk(msg.get("payload", {}))
    text = "\n".join(plain).strip()
    if len(text) < 200 and htmls:
        text = html_to_text("\n".join(htmls))
    return headers, text, pdfs


def fetch_pdfs(gm, mid, pdfs):
    out = []
    for name, ref in pdfs[:4]:
        try:
            data = _b64(ref[1]) if isinstance(ref, tuple) else gm.attachment(mid, ref)
            out.append((name, data))
        except GmailError:
            continue
    return out

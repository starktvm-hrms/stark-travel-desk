# Stark Travel Desk

Admin dashboard at **https://travel.starkpeople.in** for Stark Industries employee business travel.
It reads booking emails from a Gmail inbox, turns them into trip cards (train, flight, bus, cab, hotel),
and sends WhatsApp updates to travellers automatically. Everything runs on the Hostinger VPS that serves
starkpeople.in; the app only adds its own files and leaves the other sites alone.

```
Gmail inbox ──(Gmail API, read-only)──▶ server/ on the Hostinger VPS ──▶ SQLite (/var/lib/stark-travel)
                                            │   Stark Decoder: DeepSeek reads email text + PDF ticket text
                                            ▼
                                   WhatsApp Cloud API (Meta)
```

## What it does

- **Gmail sync** every 10 minutes (configurable). Searches for booking, ticket, ride and hotel emails
  (IRCTC, airlines, Uber/Ola, MakeMyTrip, hotels…), reads the body and attached PDF tickets.
- **Stark Decoder** (DeepSeek, `deepseek-chat` by default, JSON output mode; PDF tickets are converted to text with pypdf) extracts every leg: type, status
  (CNF / RAC / Reserved…), from/to, dates and times, train/flight/vehicle number, PNR, coach/berth/class.
- **Trip grouping**: the same PNR/booking seen again updates the existing card (status changes are logged
  and messaged); bookings for the same traveller within 3 days are grouped into one Multi-Mode trip.
  Admins can also merge trips by hand.
- **Trip cards**: mode and status, title, travellers, entry log, itinerary timeline,
  and *Track Live Schedule* / *Edit Trip* / *Send to WhatsApp*.
- **Automatic WhatsApp**: new booking itinerary, segment status changes (from emails or admin edits),
  and a departure / check-in reminder N hours before (default 3). Every send, skip and failure is logged.
- **Travellers directory**: WhatsApp numbers, other spellings ("MR TONY STARK"), per-person opt-out.
  Names on bookings are matched to it.
- Admin sign-in (PBKDF2 passwords, HttpOnly session cookie, same-origin checks, login rate limit).

## Layout

| Path | What |
| --- | --- |
| `web/` | Static dashboard (vanilla JS, no build step), served by nginx |
| `server/app.py` | HTTP API on 127.0.0.1 (stdlib), routes under `/api/` |
| `server/core.py` | Trips, grouping, WhatsApp Cloud API sending, reminders, Gmail sync loop |
| `server/decoder.py` | Stark Decoder (DeepSeek chat completions API, stdlib HTTP) |
| `server/gmail.py` | Gmail REST API client (OAuth 2.0, read-only scope) |
| `deploy/vps-setup.sh` | One-time VPS setup (nginx site, systemd, certbot, auto-update cron, backups) |

## Deploy

1. **Server (once)**, as root in hPanel → VPS → Browser terminal:
   ```bash
   curl -fsSL https://raw.githubusercontent.com/starktvm-hrms/stark-travel-desk/main/deploy/vps-setup.sh -o /tmp/travel-setup.sh && sudo bash /tmp/travel-setup.sh
   ```
   It asks for the first admin username and password. Pushes to `main` go live within 5 minutes.
2. **WhatsApp**: dashboard → Settings → WhatsApp: a permanent Meta system-user token, the sending number's
   Phone number ID, and an approved Utility template whose body is a single `{{1}}` (needed to message
   travellers who haven't written to the number in the last 24 hours).
3. **Gmail**: Settings → Gmail shows the redirect URI and the Google Cloud steps; press *Connect Gmail*.
4. **DeepSeek API key**: Settings → Stark Decoder (key from platform.deepseek.com; the account needs a balance).

Manage admins on the server:
```bash
sudo runuser -u stark-travel -- env STARK_DATA_DIR=/var/lib/stark-travel /opt/stark-travel-venv/bin/python /var/www/travel.starkpeople.in/server/app.py add-user NAME
```
Logs: `journalctl -u stark-travel -f`.

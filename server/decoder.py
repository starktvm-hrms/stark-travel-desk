"""Stark Decoder: turns a booking email (text + PDF tickets) into trip segments with Claude."""
import base64
import json

import anthropic

MODEL = "claude-opus-5-5"

SEGMENT_TYPES = ["flight", "train", "bus", "cab", "hotel", "other"]

SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["is_travel_booking", "trip_title", "travelers", "segments"],
    "properties": {
        "is_travel_booking": {
            "type": "boolean",
            "description": "True only if this email confirms, changes or cancels a real travel booking "
                           "(ticket, PNR, hotel reservation, cab ride receipt). False for marketing, OTPs, newsletters.",
        },
        "trip_title": {
            "type": "string",
            "description": "Short title, e.g. 'IRCTC Train 16345, LTT - KYJ, 20 Aug' or 'Uber ride - Kochi airport'.",
        },
        "travelers": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Passenger / guest / rider names exactly as printed. Empty if none are named.",
        },
        "segments": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["type", "status", "status_label", "origin", "destination", "date", "start_time",
                             "end_date", "end_time", "carrier", "number", "reference", "details"],
                "properties": {
                    "type": {"type": "string", "enum": SEGMENT_TYPES},
                    "status": {
                        "type": "string",
                        "enum": ["reserved", "confirmed", "waitlisted", "delayed", "completed", "cancelled"],
                        "description": "Normalised status. CNF/Booked -> confirmed; RAC/WL -> waitlisted; "
                                       "hotel reservations -> reserved; finished rides/receipts -> completed.",
                    },
                    "status_label": {"type": "string", "description": "Status as written in the email, e.g. CNF, RAC 12, Confirmed."},
                    "origin": {"type": "string", "description": "Departure place, 'City (CODE)' when a code is given. For hotels: 'Hotel Stay'."},
                    "destination": {"type": "string", "description": "Arrival place. For hotels: the hotel name."},
                    "date": {"type": ["string", "null"], "description": "Departure / check-in date, YYYY-MM-DD."},
                    "start_time": {"type": ["string", "null"], "description": "Departure / check-in time, 24h HH:MM."},
                    "end_date": {"type": ["string", "null"], "description": "Arrival / check-out date, YYYY-MM-DD."},
                    "end_time": {"type": ["string", "null"], "description": "Arrival / check-out time, 24h HH:MM."},
                    "carrier": {"type": "string", "description": "Airline, train name, cab company, hotel chain, or ''."},
                    "number": {"type": "string", "description": "Flight number, train number, or vehicle registration, or ''."},
                    "reference": {"type": "string", "description": "PNR / booking ID / confirmation number, or ''."},
                    "details": {"type": "string", "description": "One line: coach, berth, class, seat, vehicle model, room type. '' if none."},
                },
            },
        },
    },
}

SYSTEM = (
    "You read booking emails for a corporate travel desk in India and extract the itinerary. "
    "Report only what the email states; never invent dates, times, numbers or names. "
    "Use one segment per leg: each flight or train leg, each cab ride, each hotel stay. "
    "Dates in the email may be written like 20-Aug-2026 or 5/28/2026; convert them to YYYY-MM-DD. "
    "Times become 24-hour HH:MM. Indian railway station codes (LTT, KYJ, ERS) and IATA codes go in "
    "brackets after the city name when the email gives both."
)


class DecoderError(Exception):
    pass


def decode(api_key, subject, sender, received, body_text, pdfs):
    """pdfs: list of (filename, bytes). Returns the parsed dict."""
    if not api_key:
        raise DecoderError("Add a Claude API key in Settings so booking emails can be read.")
    client = anthropic.Anthropic(api_key=api_key, max_retries=3, timeout=180)
    content = []
    for name, data in pdfs[:4]:
        content.append({
            "type": "document",
            "source": {"type": "base64", "media_type": "application/pdf",
                       "data": base64.b64encode(data).decode()},
            "title": name[:200],
        })
    content.append({
        "type": "text",
        "text": f"Subject: {subject}\nFrom: {sender}\nReceived: {received}\n\n{body_text[:60000]}",
    })
    try:
        resp = client.beta.messages.create(
            model=MODEL,
            max_tokens=16000,
            system=SYSTEM,
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            output_config={"effort": "medium", "format": {"type": "json_schema", "schema": SCHEMA}},
            messages=[{"role": "user", "content": content}],
        )
    except anthropic.AuthenticationError:
        raise DecoderError("The Claude API key was rejected. Check it in Settings.")
    except anthropic.RateLimitError:
        raise DecoderError("Claude API rate limit reached; the email will be retried on the next sync.")
    except anthropic.BadRequestError as e:
        raise DecoderError(f"Claude could not read this email: {e.message}")
    except anthropic.APIStatusError as e:
        raise DecoderError(f"Claude API error {e.status_code}; will retry on the next sync.")
    except anthropic.APIConnectionError:
        raise DecoderError("Could not reach the Claude API; will retry on the next sync.")

    if resp.stop_reason == "refusal":
        raise DecoderError("Claude declined to read this email.")
    if resp.stop_reason == "max_tokens":
        raise DecoderError("The email was too long to read in one pass.")
    text = next((b.text for b in resp.content if getattr(b, "type", "") == "text"), None)
    if not text:
        raise DecoderError("Claude returned no itinerary.")
    return json.loads(text)

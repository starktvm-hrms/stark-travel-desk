"""Best-effort time zone for a place name as it appears on a ticket ("Toronto (YYZ)", "Mumbai (LTT)", "Hotel Hilton Vancouver")."""
import re
from zoneinfo import ZoneInfo, available_timezones

# IATA airport codes and city names → IANA time zone. India first, then Canada, then common business hubs.
_PLACES = {
    "Asia/Kolkata": [
        "BOM", "DEL", "BLR", "MAA", "HYD", "CCU", "COK", "TRV", "GOI", "GOX", "AMD", "PNQ", "JAI", "LKO", "CCJ", "IXE",
        "IXC", "ATQ", "BBI", "GAU", "PAT", "VNS", "NAG", "IDR", "BHO", "IXB", "VTZ", "TRZ", "IXM", "CJB", "SXR", "IXJ",
        "LTT", "CSMT", "NDLS", "SBC", "MAS", "ERS", "TVC", "KYJ", "HWH", "SC",
        "mumbai", "bombay", "delhi", "new delhi", "bengaluru", "bangalore", "chennai", "madras", "hyderabad", "kolkata",
        "calcutta", "kochi", "cochin", "ernakulam", "thiruvananthapuram", "trivandrum", "goa", "ahmedabad", "pune",
        "jaipur", "lucknow", "kozhikode", "calicut", "mangaluru", "mangalore", "chandigarh", "amritsar", "bhubaneswar",
        "guwahati", "patna", "varanasi", "nagpur", "indore", "bhopal", "visakhapatnam", "vizag", "coimbatore", "madurai",
        "tiruchirappalli", "kayamkulam", "kollam", "thrissur", "noida", "gurugram", "gurgaon", "mysuru", "mysore", "india",
    ],
    # Canada
    "America/Toronto": ["YYZ", "YTZ", "YOW", "YUL", "YQB", "toronto", "mississauga", "brampton", "markham", "ottawa",
                        "montreal", "montréal", "quebec", "québec", "waterloo", "kitchener", "hamilton", "london, on",
                        "ontario", "laval", "gatineau"],
    "America/Vancouver": ["YVR", "YYJ", "YLW", "vancouver", "victoria", "kelowna", "surrey", "burnaby", "richmond, bc",
                          "british columbia"],
    "America/Edmonton": ["YYC", "YEG", "calgary", "edmonton", "alberta"],
    "America/Winnipeg": ["YWG", "winnipeg", "manitoba"],
    "America/Regina": ["YQR", "YXE", "regina", "saskatoon", "saskatchewan"],
    "America/Halifax": ["YHZ", "YFC", "YQM", "halifax", "fredericton", "moncton", "nova scotia", "new brunswick"],
    "America/St_Johns": ["YYT", "st. john's", "st johns", "newfoundland"],
    # Gulf & Asia
    "Asia/Dubai": ["DXB", "DWC", "AUH", "SHJ", "dubai", "abu dhabi", "sharjah", "uae"],
    "Asia/Qatar": ["DOH", "doha", "qatar"],
    "Asia/Muscat": ["MCT", "muscat", "oman"],
    "Asia/Riyadh": ["RUH", "JED", "DMM", "riyadh", "jeddah", "dammam", "kuwait", "KWI", "BAH", "bahrain"],
    "Asia/Singapore": ["SIN", "singapore"],
    "Asia/Kuala_Lumpur": ["KUL", "kuala lumpur", "malaysia"],
    "Asia/Bangkok": ["BKK", "DMK", "bangkok", "phuket", "HKT"],
    "Asia/Hong_Kong": ["HKG", "hong kong"],
    "Asia/Shanghai": ["PVG", "PEK", "PKX", "CAN", "SZX", "shanghai", "beijing", "shenzhen", "guangzhou"],
    "Asia/Tokyo": ["NRT", "HND", "KIX", "tokyo", "osaka"],
    "Asia/Seoul": ["ICN", "seoul"],
    "Asia/Colombo": ["CMB", "colombo", "sri lanka"],
    "Asia/Kathmandu": ["KTM", "kathmandu", "nepal"],
    "Asia/Dhaka": ["DAC", "dhaka", "bangladesh"],
    "Australia/Sydney": ["SYD", "sydney", "canberra", "CBR"],
    "Australia/Melbourne": ["MEL", "melbourne"],
    # Europe
    "Europe/London": ["LHR", "LGW", "STN", "LCY", "MAN", "EDI", "london", "manchester", "edinburgh", "uk"],
    "Europe/Paris": ["CDG", "ORY", "paris"],
    "Europe/Berlin": ["FRA", "MUC", "BER", "frankfurt", "munich", "berlin"],
    "Europe/Amsterdam": ["AMS", "amsterdam"],
    "Europe/Zurich": ["ZRH", "GVA", "zurich", "geneva"],
    "Europe/Istanbul": ["SAW", "istanbul"],
    # United States
    "America/New_York": ["JFK", "EWR", "LGA", "BOS", "IAD", "DCA", "ATL", "MIA", "new york", "newark", "boston",
                         "washington", "atlanta", "miami"],
    "America/Chicago": ["ORD", "MDW", "DFW", "IAH", "chicago", "dallas", "houston"],
    "America/Denver": ["DEN", "denver"],
    "America/Los_Angeles": ["SFO", "LAX", "SEA", "SJC", "san francisco", "los angeles", "seattle", "san jose"],
}

_CODE = {}
_NAME = []
for _tz, _items in _PLACES.items():
    for _x in _items:
        if _x.isupper():
            _CODE[_x] = _tz
        else:
            _NAME.append((_x, _tz))
_NAME.sort(key=lambda p: -len(p[0]))  # longest names first ("new delhi" before "delhi")

VALID = available_timezones()


def valid_tz(tz):
    return bool(tz) and tz in VALID


def guess_tz(place, seg_type=""):
    """IANA zone for a place string, or '' if unknown. Bracketed codes win, then city names, then bare codes."""
    if not place:
        return ""
    text = str(place)
    for code in re.findall(r"\(([A-Z]{2,4})\)", text):
        if code in _CODE:
            return _CODE[code]
    low = " " + re.sub(r"\s+", " ", text.lower()) + " "
    for name, tz in _NAME:
        if re.search(r"(?<![a-z])" + re.escape(name) + r"(?![a-z])", low):
            return tz
    for code in re.findall(r"\b([A-Z]{3})\b", text):
        if code in _CODE:
            return _CODE[code]
    if seg_type == "train":
        return "Asia/Kolkata"  # the desk's trains are Indian Railways
    return ""


def check_tz(tz):
    """Validated zone or ''."""
    tz = (tz or "").strip()
    if not tz:
        return ""
    try:
        ZoneInfo(tz)
        return tz if tz in VALID else ""
    except Exception:  # noqa: BLE001
        return ""

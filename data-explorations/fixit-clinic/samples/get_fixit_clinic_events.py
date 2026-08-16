"""Fetch events from the public 'Fixit Clinic Programs' Google Calendar.

The calendar is embedded at:
    https://fixitclinic.blogspot.com/p/fixit-clinic-events-calendar.html

The embed's `src` decodes to the calendar ID below, which exposes a public
iCalendar feed at the URL constructed in ICS_URL.
"""

from __future__ import annotations

import json
import re
import sys
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Iterator

CALENDAR_ID = "tvb554o4bdds5lk9g6692d1svc@group.calendar.google.com"
ICS_URL = (
    "https://calendar.google.com/calendar/ical/"
    f"{urllib.parse.quote(CALENDAR_ID, safe='')}/public/basic.ics"
)


@dataclass
class Event:
    uid: str
    summary: str
    location: str
    location_name: str
    location_address: str
    location_city: str
    location_zip: str
    description: str
    start: str
    end: str


_STATE_ZIP_RE = re.compile(r"^[A-Z]{2}\s+(\d{5}(?:-\d{4})?)$")


def parse_location(location: str) -> tuple[str, str, str, str]:
    """Split a Google-formatted address into (name, address, city, zip).

    Typical form: "Name, Street, City, MA 02139, USA". The name part is optional
    (e.g. "486 Main St, Acton, MA 01720, USA"). Returns empty strings for parts
    that can't be identified.
    """
    if not location:
        return "", "", "", ""
    parts = [p.strip() for p in location.split(",") if p.strip()]
    # Drop trailing country.
    if parts and parts[-1].upper() in {"USA", "US", "UNITED STATES"}:
        parts.pop()
    # Extract zip from trailing "STATE ZIP" token.
    zip_code = ""
    if parts:
        m = _STATE_ZIP_RE.match(parts[-1])
        if m:
            zip_code = m.group(1)
            parts.pop()
    if not parts:
        return location, "", "", zip_code
    city = parts.pop() if len(parts) > 1 else ""
    if len(parts) >= 2:
        name = parts[0]
        address = ", ".join(parts[1:])
    elif len(parts) == 1:
        token = parts[0]
        # If it starts with a number, treat as address; otherwise as a venue name.
        if token[:1].isdigit():
            name, address = "", token
        else:
            name, address = token, ""
    else:
        name, address = "", ""
    return name, address, city, zip_code


def fetch_ics(url: str = ICS_URL) -> str:
    with urllib.request.urlopen(url, timeout=30) as resp:
        return resp.read().decode("utf-8")


def _unfold(ics: str) -> list[str]:
    # RFC 5545: lines beginning with a space or tab continue the previous line.
    lines: list[str] = []
    for raw in ics.splitlines():
        if raw.startswith((" ", "\t")) and lines:
            lines[-1] += raw[1:]
        else:
            lines.append(raw)
    return lines


def _unescape(value: str) -> str:
    return (
        value.replace("\\N", "\n")
        .replace("\\n", "\n")
        .replace("\\,", ",")
        .replace("\\;", ";")
        .replace("\\\\", "\\")
    )


def _parse_dt(value: str) -> str:
    # Handles forms like 20260615T180000Z, 20260615T180000, and 20260615 (all-day).
    try:
        if value.endswith("Z"):
            dt = datetime.strptime(value, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
            return dt.isoformat()
        if "T" in value:
            return datetime.strptime(value, "%Y%m%dT%H%M%S").isoformat()
        return datetime.strptime(value, "%Y%m%d").date().isoformat()
    except ValueError:
        return value


def parse_events(ics: str) -> Iterator[Event]:
    in_event = False
    fields: dict[str, str] = {}
    for line in _unfold(ics):
        if line == "BEGIN:VEVENT":
            in_event = True
            fields = {}
            continue
        if line == "END:VEVENT":
            in_event = False
            location = _unescape(fields.get("LOCATION", ""))
            name, address, city, zip_code = parse_location(location)
            yield Event(
                uid=fields.get("UID", ""),
                summary=_unescape(fields.get("SUMMARY", "")),
                location=location,
                location_name=name,
                location_address=address,
                location_city=city,
                location_zip=zip_code,
                description=_unescape(fields.get("DESCRIPTION", "")),
                start=_parse_dt(fields.get("DTSTART", "")),
                end=_parse_dt(fields.get("DTEND", "")),
            )
            continue
        if not in_event or ":" not in line:
            continue
        key_part, _, value = line.partition(":")
        # Strip parameters: e.g. DTSTART;TZID=America/Los_Angeles
        key = key_part.split(";", 1)[0]
        fields[key] = value


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(f"usage: {argv[0]} <output.json>", file=sys.stderr)
        return 2
    out_path = argv[1]
    ics = fetch_ics()
    events = [e for e in parse_events(ics) if e.summary.startswith("USA-MA")]
    events.sort(key=lambda e: e.start)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump([asdict(e) for e in events], f, indent=2)
        f.write("\n")
    print(f"Wrote {len(events)} events to {out_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

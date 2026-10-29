# Beacon Time Manager

A lightweight weekly planner for Bushnell student-athletes: recurring personal activities, dated calendar imports, goals, reminders, and landscape printing. Uses the supplied B-and-torch logo and saves data in the same browser.

## Run locally

Requires Python 3.9+ with the IANA timezone database (Python 3.12 tested). On Windows, if `America/Los_Angeles` is unavailable, install the official `tzdata` package with `py -m pip install tzdata`.

```sh
cd beacon-planner
python server.py
```

On Windows, `py server.py` also works. Open `http://localhost:8000` in your browser. Keep the terminal running. Both automatic schedule requests and `.ics` import require this server; opening the HTML file directly is insufficient. The application itself has no JavaScript package dependencies or third-party analytics.

## Calendar status and dates

On October 29, 2026, the official baseball schedule page was reachable, but the prototype's `https://bushnellbeacons.com/calendar.ashx?path=baseball` feed returned **404**. Automatic sport schedules are **not verified or production-ready**. Other sport identifiers and feeds remain unverified. The app reports failure and keeps saved events. Use the official schedule link to confirm competitions, or import an official `.ics` calendar file. No real competition data is bundled, and test fixtures are not official events.

Calendar import accepts up to 2 MB. UTC and IANA `TZID` values are supported. Floating timestamps default to `America/Los_Angeles`, with winter/summer offsets. Timed events display in the device's timezone; all-day events keep their calendar dates and use exclusive end dates. All-day and pre-8 AM competitions appear above the hourly grid. Events without an end display with a one-hour fallback. Cancellation status hides an event; reimporting the same UID updates it rather than adding a duplicate. For ambiguous fall-back wall times, the first occurrence is used unless the feed supplies UTC. Invalid spring-forward times are skipped.

Recurring ICS rules, recurrence exceptions, custom `VTIMEZONE` definitions and non-IANA timezone names are unsupported; affected entries are counted as skipped. Personal weekday repetition is supported independently. Cross-midnight timed events currently display on their start day through midnight; continuation on the next day is not implemented. Previously imported calendars from the original prototype retain their stored timestamps; reimport to apply corrected timezone parsing.

## Verification

From the repository root:

```sh
python -m unittest discover -s beacon-planner/tests -v
```

Six tests cover Pacific DST and winter/summer offsets, explicit timezones and UTC, all-day dates, duplicate updates/cancellations, escaped/folded content, and invalid/unsupported entries.

Optional browser checks require Python Playwright and `/usr/bin/chromium` (both available in the prepared cloud environment). Start the server, then run:

```sh
python beacon-planner/tests/browser_smoke.py
```

Checks include activity/goal/reminder persistence, fixture calendar import and deduplication, correct winter event day/hour, all-day dates, sport switching, week navigation, mobile overflow at 375/390/768 pixels, and modal dismissal. It generates a populated PDF and screenshots under `/tmp/beacon-browser-check`; override with `BEACON_TEST_ARTIFACTS`. Browser calendar responses use clearly labeled test fixtures. They do not prove official schedule integration.

Printing uses US Letter landscape. The checked filled week fits one page with all seven days and the 8 AM–midnight grid. Arbitrarily dense overlapping activities or many all-day entries can exceed the available space; inspect print preview before saving. Mobile uses a horizontally scrollable seven-day calendar.

## Privacy and deployment

Data lives in browser `localStorage`, does not sync across devices, and can be lost when browser storage is cleared. Reminders require the page to remain open. Calendar files are parsed by the Python server and are not intentionally saved there. No JSON backup/restore controls are exposed.

This is a local development server bound to loopback, not a public deployment. A public site will need an appropriate production host/server, HTTPS, reviewed security and privacy behavior, and a verified official schedule source. Publishing a Codex development environment does not deploy this website.

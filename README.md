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

The planner reads the **public official athletics schedule pages** at `bushnellbeacons.com/sports/<sport>/schedule`. Selecting a sport loads its competitions, keeps personal classes intact, and jumps to the next competition week (or latest listed week if the season has ended). “This week” returns to today; “Next competition” jumps back to the next listed event.

On October 29, 2026, the integration was checked against the official baseball, men's basketball, and women's volleyball pages. The original `calendar.ashx` feed returned 404 and is no longer used. Volleyball's correct source path is `womens-volleyball`. The remaining offered sports use schedule paths published in the official navigation but have not each received individual end-to-end checks. Unsupported page formats fail visibly instead of producing invented events.

The parser joins competition years from the page's structured event data with the **visible opponent/date/start time**. This is intentional: the baseball page displayed 11 a.m. for a competition whose embedded metadata incorrectly said 11 p.m. Unpublished start times remain TBA above the grid, and date ranges retain their days. Times without an explicit zone are interpreted in Pacific time; explicit MT/CT/ET/PT labels are honored. Confirm timezones and last-minute changes with athletics. Official durations are not published; a one-hour display block is a visual placeholder, not a promised game length.

Responses are cached for 15 minutes. The integration checks `robots.txt`, respects disallowed paths, and waits at least 30 seconds between source requests. An uncached initial load may take 30–45 seconds; switching to another uncached sport can also require a wait. Source URL, last fetch time, and skipped-entry counts are available in the API; the UI shows last-check time and warnings. The adapter depends on the official page format, so athletics markup changes may require maintenance.

## Classes and colors

Click **Add activity** or an empty calendar time to create a class. Click any personal activity block to edit its class/name, category, start/end time, recurring days, or custom block color. Changes apply to its selected repeating weekdays and are saved in the same browser. Text color adjusts to the block color for contrast. Official competition blocks show source details and are not personal class entries.

Calendar import accepts up to 2 MB. UTC and IANA `TZID` values are supported. Floating timestamps default to `America/Los_Angeles`, with winter/summer offsets. Timed events display in the device's timezone; all-day events keep their calendar dates and use exclusive end dates. All-day and pre-8 AM competitions appear above the hourly grid. Events without an end display with a one-hour fallback. Cancellation status hides an event; reimporting the same UID updates it rather than adding a duplicate. For ambiguous fall-back wall times, the first occurrence is used unless the feed supplies UTC. Invalid spring-forward times are skipped.

Recurring ICS rules, recurrence exceptions, custom `VTIMEZONE` definitions and non-IANA timezone names are unsupported; affected entries are counted as skipped. Personal weekday repetition is supported independently. Cross-midnight timed events currently display on their start day through midnight; continuation on the next day is not implemented. Previously imported calendars from the original prototype retain their stored timestamps; reimport to apply corrected timezone parsing.

## Verification

From the repository root:

```sh
python -m unittest discover -s beacon-planner/tests -v
```

Thirteen tests cover Pacific DST and winter/summer offsets, explicit timezones and UTC, all-day dates, duplicate updates/cancellations, invalid entries, official-page parsing, visible-versus-metadata time discrepancies, TBA dates, ranked opponents, source caching, and robots rules. Minimal source excerpts in tests/fixtures are captured official examples, not fabricated games.

Optional browser checks require Python Playwright and `/usr/bin/chromium` (both available in the prepared cloud environment). Start the server, then run:

```sh
python beacon-planner/tests/browser_smoke.py
```

Checks include activity/goal/reminder persistence, editing class names and colors, fixture calendar import and deduplication, correct winter event day/hour, all-day dates, sport switching, week navigation, mobile overflow at 375/390/768 pixels, and modal dismissal. It generates a populated PDF and screenshots under `/tmp/beacon-browser-check`; override with `BEACON_TEST_ARTIFACTS`. Browser calendar responses use clearly labeled test fixtures. They do not prove official schedule integration.

The opt-in live browser check uses real API responses without fixture interception:

```sh
python beacon-planner/tests/live_schedule_smoke.py
```

It selects baseball, men's basketball, and women's volleyball, verifies the next competition appears in the grid (or TBA date area), switches back to a cached sport without duplicates, and checks that a personal class and its color survive. It generates official-data screenshots and a PDF under `/tmp/beacon-live-check`. Expect up to two minutes for uncached requests because of the site's crawl delay.

Printing uses US Letter landscape. The checked filled week fits one page with all seven days and the 8 AM–midnight grid. Arbitrarily dense overlapping activities or many all-day entries can exceed the available space; inspect print preview before saving. Mobile uses a horizontally scrollable seven-day calendar.

## Privacy and deployment

Data lives in browser `localStorage`, does not sync across devices, and can be lost when browser storage is cleared. Reminders require the page to remain open. Calendar files are parsed by the Python server and are not intentionally saved there. No JSON backup/restore controls are exposed.

This is a local development server bound to loopback, not a public deployment. A public site will need an appropriate production host/server, HTTPS, reviewed security and privacy behavior, and maintenance of the official schedule adapter. Publishing a Codex development environment does not deploy this website.

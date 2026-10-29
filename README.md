# Beacon Time Manager

A lightweight weekly planner for Bushnell student-athletes: recurring personal activities, dated calendar imports, goals, reminders, and landscape printing. Uses the supplied B-and-torch logo and saves data in the same browser.

## Run locally

Requires Python 3.9+ with the IANA timezone database (Python 3.12 tested). On Windows, if `America/Los_Angeles` is unavailable, install the official `tzdata` package with `py -m pip install tzdata`.

```sh
cd beacon-planner
python server.py
```

On Windows, `py server.py` also works. Open `http://localhost:8000` in your browser. Keep the terminal running. Both automatic schedule requests and `.ics` import require this server; opening the HTML file directly is insufficient. No JavaScript package installation is needed. A pinned local copy of jsPDF 4.2.1 is included for browser PDF creation; its MIT license is in vendor/jspdf.LICENSE. There are no third-party analytics.

## Website layouts, daily scripture, and schedule downloads

Use **Planner view** to switch between Dashboard (weekly grid and sidebar), Calendar focus (full-width grid with tools below), and Daily agenda (day selector and larger editable activity cards). The preference stays saved in the same browser. All views use the same saved activities and official competitions.

The sidebar's **Verse of the day** requests **NIV** from Bible Gateway's public verse-of-the-day widget via the Python server. The server parses the payload as data without executing remote JavaScript, so the publisher's script cannot access personal planner data. It displays the source reference, link, and publisher attribution returned by the provider. No NIV verse collection is bundled or persisted, and another translation is never substituted. The running Python server requires internet access to `www.biblegateway.com`; responses are cached for 15 minutes. The widget is re-requested when the local date changes; the provider determines its daily selection. If the service fails, the card offers retry and a direct NIV link. PDFs may include a successfully loaded verse with its publisher attribution.

Live Bible Gateway access was blocked by the cloud network policy during development. A draft domain allowance for `biblegateway.com` was saved but has not been applied or published. Provider-response handling and failures were tested with clearly labeled synthetic fixtures, not real NIV text. Live service behavior remains unverified until that access is enabled.
Use **Print / Download** to choose an actual downloadable PDF:

- Weekly grid: one compact landscape page; long labels may shorten.
- Weekly agenda: portrait lists with full activity names, times, and locations.
- Daily pages: a portrait page per day with writing space; dense days continue onto extra pages.

Choose US Letter or A4, grayscale, and whether to include today's verse. Downloads include the displayed week's saved activities and loaded competitions, including TBA entries. PDFs are created in the browser; personal data is not uploaded for export. **Preview / Print** opens the PDF in a new tab, where the browser's PDF viewer provides printing controls. The standard PDF font supports Latin text; other scripts may need an embedded-font enhancement.

Optional verification, with the server running:

```sh
python beacon-planner/tests/browser_features.py
```

This exercises all three website layouts, persistent preferences, agenda editing, mobile widths, NIV payload/attribution handling, daily refresh, and provider-failure behavior, actual PDF downloads in all three layouts, A4/grayscale, and the print preview. Artifacts are written under `/tmp/beacon-feature-check`.

## Shared academic dates and holiday shading

University academic dates are a shared layer, separate from personal activities and sport selection. Read-only entries appear in every view and PDF export. Holiday columns use a pale gold background; break columns use pale blue, with text labels so color is not the only indication. Personal activities are preserved, including recurring classes; shading does not automatically cancel them.

The central source file is `beacon-planner/academic-calendar.json`. Events use date-only `start` and exclusive `end`, an ID/title, and `kind` (`holiday`, `break`, `deadline`, or `term`). Only verified data is displayed. The official page at https://bushnell.edu/academics/academic-calendars/ was blocked by the environment network policy. No university dates have been guessed: the shipped data remains unverified and empty pending the actual on-campus academic calendar. A draft allowance for `bushnell.edu` is saved but unapplied. Browser holiday tests use clearly labeled synthetic fixtures, not official dates. Verify the program and academic year against the official source before populating this file and setting `verified` to true.

## Calendar status and dates

The planner reads the **public official athletics schedule pages** at `bushnellbeacons.com/sports/<sport>/schedule`. Selecting a sport loads its competitions, keeps personal classes intact, and jumps to the next competition week (or latest listed week if the season has ended). “This week” returns to today; “Next competition” jumps back to the next listed event.

On October 29, 2026, the integration was checked against the official baseball, men's basketball, and women's volleyball pages. The original `calendar.ashx` feed returned 404 and is no longer used. Volleyball's correct source path is `womens-volleyball`. The remaining offered sports use schedule paths published in the official navigation but have not each received individual end-to-end checks. Unsupported page formats fail visibly instead of producing invented events.

The parser joins competition years from the page's structured event data with the **visible opponent/date/start time**. This is intentional: the baseball page displayed 11 a.m. for a competition whose embedded metadata incorrectly said 11 p.m. Unpublished start times remain TBA above the grid, and date ranges retain their days. Times without an explicit zone are interpreted in Pacific time; explicit MT/CT/ET/PT labels are honored. Confirm timezones and last-minute changes with athletics. Official durations are not published; a one-hour display block is a visual placeholder, not a promised game length.

Responses are cached for 15 minutes. The integration checks `robots.txt`, respects disallowed paths, and waits at least 30 seconds between source requests. An uncached initial load may take 30–45 seconds; switching to another uncached sport can also require a wait. Source URL, last fetch time, and skipped-entry counts are available in the API; the UI shows last-check time and warnings. The adapter depends on the official page format, so athletics markup changes may require maintenance.

## University and athletics wording

The planner uses Bushnell's mission themes (Wisdom, Faith, Service), the university mission and vision text supplied by the project owner, and the official athletics Tri-Athlete model (Character, Classroom, Competition). The banner links to [Mission & Vision](https://bushnell.edu/about/mission-vision/) and the [Tri-Athlete model](https://bushnellbeacons.com/sports/growth). The athletics content was verified from its page; direct access to the university mission page was blocked in this development environment, so its wording was supplied by the owner. Promotional slogans have been removed.

## Classes and colors

Click **Add activity** or an empty calendar time to create a class. Click any personal activity block to edit its class/name, category, start/end time, recurring days, or custom block color. Changes apply to its selected repeating weekdays and are saved in the same browser. Text color adjusts to the block color for contrast. Official competition blocks show source details and are not personal class entries.

Calendar import accepts up to 2 MB. UTC and IANA `TZID` values are supported. Floating timestamps default to `America/Los_Angeles`, with winter/summer offsets. Timed events display in the device's timezone; all-day events keep their calendar dates and use exclusive end dates. All-day and pre-8 AM competitions appear above the hourly grid. Events without an end display with a one-hour fallback. Cancellation status hides an event; reimporting the same UID updates it rather than adding a duplicate. For ambiguous fall-back wall times, the first occurrence is used unless the feed supplies UTC. Invalid spring-forward times are skipped.

Recurring ICS rules, recurrence exceptions, custom `VTIMEZONE` definitions and non-IANA timezone names are unsupported; affected entries are counted as skipped. Personal weekday repetition is supported independently. Cross-midnight timed events currently display on their start day through midnight; continuation on the next day is not implemented. Previously imported calendars from the original prototype retain their stored timestamps; reimport to apply corrected timezone parsing.

## Verification

From the repository root:

```sh
python -m unittest discover -s beacon-planner/tests -v
```

Sixteen tests cover Pacific DST and winter/summer offsets, explicit timezones and UTC, all-day dates, duplicate updates/cancellations, invalid entries, official-page parsing, visible-versus-metadata time discrepancies, TBA dates, ranked opponents, source caching, robots rules, and safe NIV payload/attribution parsing. Minimal source excerpts in tests/fixtures are captured official examples, not fabricated games.

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

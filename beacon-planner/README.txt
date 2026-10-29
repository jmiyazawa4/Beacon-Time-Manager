BEACON TIME MANAGER

Run locally with Python 3:
  cd beacon-planner
  python server.py
On Windows: py server.py
Then open http://localhost:8000 in your browser.

See ../README.md for calendar status, timezone behavior, tests, and limitations.
Sport selection reads the public official athletics schedule pages. Baseball,
men's basketball, and women's volleyball were checked on October 29, 2026.
Uncached requests can take 30-45 seconds to respect the site's crawl delay.
Times not published by athletics remain TBA. Confirm changes with athletics.
Click a personal calendar block to edit its class name, time, days, and color.

Local browser storage is device-specific. Reminders require the page to be open.
This server is for local development and has not been publicly deployed.

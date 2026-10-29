BEACON TIME MANAGER

Run locally with Python 3:
  cd beacon-planner
  python server.py
On Windows: py server.py
Then open http://localhost:8000 in your browser.

See ../README.md for calendar status, timezone behavior, tests, and limitations.
Automatic sport loading is not verified: the tested baseball feed returned 404
on October 29, 2026. Use the official schedule link or import an official .ics
file through the running server. No events are invented.

Local browser storage is device-specific. Reminders require the page to be open.
This server is for local development and has not been publicly deployed.

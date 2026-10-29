# Security and privacy status

This is a security baseline, not a guarantee against breaches or a compliance certification. The live backend has not been publicly deployed. The separate `gh-pages` branch is a review-only static preview with mandatory private sessions; do not enter real student information there.

## Data handling

| Data | Where it goes |
| --- | --- |
| Optional name/nickname, classes, personal activities, goals, reminders | This browser profile only. Normal mode uses unencrypted localStorage; private-session mode keeps them in page memory. |
| Calendar-file imports | Parsed locally in the browser. No calendar file or filename is uploaded. |
| Official sports requests | Only an allowlisted sport slug is sent to the application. The server retrieves public athletics pages. |
| NIV requests | A public verse request goes through the server; student planner details are not forwarded. Publisher scripts are parsed as data, never executed. |
| Academic calendar | Shared public university dates, with owner-supplied provenance. |
| PDF exports | Generated in the browser and saved wherever the user chooses. They contain schedule information and are outside the site's control afterward. |
| Connection metadata | The hosting provider/reverse proxy may receive client IPs and request URLs. Its logs, retention, location, and access must be reviewed separately. |

The app has no student-account database, public profiles, tracking pixels, third-party analytics, or automatic sharing. Browser notifications are opt-in and use generic text instead of the reminder's contents. Students should avoid entering IDs, grades, health details, or information about other people.

## Implemented protections

- A same-origin Content Security Policy permits only bundled scripts and the exact main-script hash; it does not permit unsafe JavaScript evaluation. Inline CSS remains allowed for the calendar's dynamic positioning. `nosniff`, no-referrer, framing denial, opener/resource isolation, and restrictive camera/microphone/location policies are included.
- The server serves an explicit public-file allowlist anchored to the application directory. Source files, configuration, tests, directory listings, path traversal, and symlinks escaping that root are not served.
- The HTTP/WSGI interface is read-only. It rejects planner writes and uploads without reading request bodies. Cross-site API requests, unknown query parameters, unconfigured hostnames, and unsupported sports are rejected.
- Calendar parsing limits file bytes, line count, event count, title/location lengths, and supported date/time formats. Embedded HTML remains text; calendar URLs/attachments are not fetched. Invalid dates, unsupported recurrence, and DST gaps are rejected or counted as skipped.
- Four source requests can run concurrently per application process. The production server uses one process/eight threads, request header/URL bounds, finite timeouts, and worker recycling. Source caches and the athletics crawl delay are retained. This does not replace a host's traffic/rate-limit protections.
- Routine app access logs are disabled, and public errors do not include internal exceptions. Production-server error logs and host/proxy logs can still include connection/security metadata and need their own retention and access controls.
- Private-session mode removes this app's durable planner entry and stops saving new entries. Other open planner tabs receive the mode change and stop resaving data. Reload/page exit clears private in-memory state. Older downloads, screenshots, browser/device backups, and other copies cannot be erased by this feature. A storage-removal failure is reported instead of claiming old data is gone.
- The review-only hosted preview additionally locks private-session mode on and includes a static CSP. It uses saved public sports snapshots and has no live backend. GitHub Pages shares an origin across an owner's project sites; it is not the final student-data hosting environment.
- Gunicorn is pinned by version and artifact hash in `requirements-production.txt`. Browser jsPDF is vendored with its license. These dependencies still require ongoing monitoring and updates.

## Before students use a hosted release

1. Choose a host and dedicated origin approved for the intended university use. Decide who administers it and handles privacy/security reports. Do not claim FERPA or other compliance based on these changes.
2. Enable managed HTTPS, enforce HTTP-to-HTTPS redirects, and validate the actual certificate and redirects. Set `BEACON_HTTPS=1` only behind the configured HTTPS proxy so the application sends HSTS. HTTPS has not been enabled or verified in this local workspace.
3. Set `BEACON_ALLOWED_HOSTS` to the exact public hostname. Keep the app behind the host's supported reverse proxy. Configure its body limits, rate/traffic protections, logs, retention, administrative access, and account MFA.
4. Run the production and browser security tests on the deployed origin, verify headers and PDF downloads, and confirm no personal planner data appears in network requests or logs.
5. Have the school review the data handling, shared-device behavior, source/publisher usage, and privacy wording before rollout. Establish an update and incident-response owner.
6. If cloud sync, rosters, accounts, or cross-device persistence are added, perform a new design review: real authentication (preferably school SSO), per-user authorization, managed encrypted storage, retention/deletion rules, and audit controls will be necessary.

## Production launch preparation

Use a production WSGI server, not Python's development HTTP server:

```sh
python -m pip install --require-hashes -r requirements-production.txt
cd beacon-planner
# Host settings supply PORT, BEACON_ALLOWED_HOSTS, and BEACON_HTTPS.
gunicorn --config gunicorn.conf.py webapp:application
```

Local production test (HTTP only, no HSTS assertion about a real TLS connection):

```sh
cd beacon-planner
PORT=8001 /path/to/venv/bin/gunicorn --config gunicorn.conf.py webapp:application
```

Validation from the repository root:

```sh
python -m unittest discover -s beacon-planner/tests -v
node beacon-planner/tests/calendar_import.test.js
BEACON_TEST_URL=http://127.0.0.1:8001 python beacon-planner/tests/browser_features.py
BEACON_TEST_URL=http://127.0.0.1:8001 python beacon-planner/tests/browser_privacy_security.py
```

The browser test observes outgoing requests for synthetic private markers, imports hostile calendar text without uploads, checks CSP enforcement and private-mode behavior across tabs/reload, and verifies generic notification text. No third-party security audit or live hosting security certification has been performed.

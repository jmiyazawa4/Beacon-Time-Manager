"""Optional browser checks: run with a local server and Python Playwright installed."""
import os
from datetime import datetime, timezone
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE = os.environ.get('BEACON_TEST_URL', 'http://127.0.0.1:8000')
OUT = Path(os.environ.get('BEACON_TEST_ARTIFACTS', '/tmp/beacon-browser-check'))
OUT.mkdir(parents=True, exist_ok=True)
ICS = b'''BEGIN:VCALENDAR\r
BEGIN:VEVENT\r
UID:timezone-fixture\r
DTSTART;TZID=America/Los_Angeles:20260115T120000\r
DTEND;TZID=America/Los_Angeles:20260115T133000\r
SUMMARY:Fixture winter game\r
END:VEVENT\r
BEGIN:VEVENT\r
UID:all-day-fixture\r
DTSTART;VALUE=DATE:20260116\r
DTEND;VALUE=DATE:20260118\r
SUMMARY:Fixture all-day meet\r
END:VEVENT\r
END:VCALENDAR'''

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path='/usr/bin/chromium', headless=True, args=['--no-sandbox'])
    page = browser.new_page(timezone_id='America/Los_Angeles', viewport={'width': 1440, 'height': 1000})
    page.clock.install(time=datetime(2026, 1, 15, 20, tzinfo=timezone.utc))
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    # Keep live athletics checks separate from deterministic browser fixtures.
    page.route('**/api/schedule?*', lambda route: route.fulfill(status=502, content_type='application/json', body='{"error":"Fixture feed unavailable","detail":"Use calendar import."}'))
    page.add_init_script("""if (!localStorage.getItem('beacon-planner-v1')) localStorage.setItem('beacon-planner-v1', JSON.stringify({student:'Browser test',sport:'',datedEvents:[],events:[],goals:[],reminders:[]}));""")
    page.goto(BASE)
    page.locator('#add').click()
    page.locator('#evName').fill('Long biology class and collaborative study session')
    page.locator('#evStart').select_option('540')
    page.locator('#evEnd').select_option('660')
    for checkbox in page.locator('#dayChoices input').all():
        checkbox.check()
    page.locator('#saveEvent').click()
    assert not page.locator('#modal').is_visible()
    page.locator('#goalInput').fill('Finish assignment')
    page.locator('#addGoal').click()
    page.locator('#reminderText').fill('Bring textbook')
    page.locator('#reminderAt').fill('2099-01-15T08:00')
    page.locator('#addReminder').click()
    page.reload()
    assert 'Long biology class' in page.locator('#calendar').inner_text()
    assert 'Finish assignment' in page.locator('#goals').inner_text()
    assert 'Bring textbook' in page.locator('#reminders').inner_text()
    page.locator('.event').first.click()
    page.locator('#evName').fill('Edited biology class')
    page.locator('#evColor').fill('#f6c642')
    page.locator('#saveEvent').click()
    page.reload()
    saved = page.evaluate("JSON.parse(localStorage.getItem('beacon-planner-v1'))")
    assert saved['events'][0]['name'] == 'Edited biology class'
    assert saved['events'][0]['color'] == '#f6c642'
    assert page.locator('.event').first.evaluate('(e)=>getComputedStyle(e).backgroundColor') == 'rgb(246, 198, 66)'
    page.locator('.event').first.click()
    page.locator('#evName').fill('Long biology class and collaborative study session')
    page.locator('#saveEvent').click()
    page.locator('#sport').select_option('baseball')
    page.wait_for_function("document.getElementById('sportStatus').textContent.includes('Fixture feed unavailable')")
    assert 'Long biology class' in page.locator('#calendar').inner_text()
    assert 'Jan 11' in page.locator('#weekLabel').inner_text()
    page.locator('#nextWeek').click()
    assert 'Jan 18' in page.locator('#weekLabel').inner_text()
    assert 'Long biology class' in page.locator('#calendar').inner_text()
    page.locator('#prevWeek').click()
    for _ in range(2):
        page.locator('#sportCalendarFile').set_input_files({'name': 'fixture.ics', 'mimeType': 'text/calendar', 'buffer': ICS})
        page.wait_for_function("document.getElementById('sportStatus').textContent.includes('Imported or updated 2')")
    state = page.evaluate("JSON.parse(localStorage.getItem('beacon-planner-v1'))")
    assert len(state['datedEvents']) == 2, state
    game = page.locator('.slot[data-day="4"][data-hour="12"] .official-event')
    assert game.count() == 1 and 'Fixture winter game' in game.inner_text()
    assert page.locator('#calendarNotes').inner_text().count('Fixture all-day meet') == 2
    assert 'Fri 1/16' in page.locator('.dayhead').nth(5).inner_text()
    page.locator('#sport').select_option('softball')
    assert page.locator('.official-event').count() == 0
    assert 'Long biology class' in page.locator('#calendar').inner_text()
    page.locator('#sport').select_option('baseball')
    assert game.count() == 1
    # Add a late event to catch clipping at the bottom of the printed week.
    page.locator('#add').click()
    page.locator('#evName').fill('Late evening study')
    page.locator('#evStart').select_option('1380')
    page.locator('#evEnd').select_option('1440')
    page.locator('#saveEvent').click()
    page.pdf(path=str(OUT / 'filled-week.pdf'), prefer_css_page_size=True, print_background=True)
    page.screenshot(path=str(OUT / 'desktop.png'), full_page=True)
    for width in (375, 390, 768):
        page.set_viewport_size({'width': width, 'height': 844})
        assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth'), (width, page.evaluate('document.documentElement.scrollWidth'))
        page.locator('#add').click()
        assert page.locator('#evName').is_visible()
        page.keyboard.press('Escape')
        assert not page.locator('#modal').is_visible()
    page.set_viewport_size({'width': 390, 'height': 844})
    page.screenshot(path=str(OUT / 'mobile.png'), full_page=True)
    assert not errors, errors
    print('PASS: activities/goals/reminders survive reload; import dates, deduplication, sport switching, mobile widths, dialog keyboard dismissal; no browser errors')
    print('PDF and screenshots:', OUT)
    browser.close()

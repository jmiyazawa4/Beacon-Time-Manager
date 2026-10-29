"""Opt-in live check; start server.py first. Makes real athletics requests."""
from datetime import datetime, timezone
from pathlib import Path
import os
from playwright.sync_api import sync_playwright

OUT = Path(os.environ.get('BEACON_TEST_ARTIFACTS', '/tmp/beacon-live-check'))
OUT.mkdir(parents=True, exist_ok=True)
with sync_playwright() as p:
    browser = p.chromium.launch(executable_path='/usr/bin/chromium', headless=True, args=['--no-sandbox'])
    page = browser.new_page(viewport={'width': 1440, 'height': 1000}, timezone_id='America/Los_Angeles')
    page.set_default_timeout(90000)
    page.clock.install(time=datetime(2026, 10, 29, 20, tzinfo=timezone.utc))
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.goto(os.environ.get('BEACON_TEST_URL', 'http://127.0.0.1:8000'))
    page.locator('#add').click()
    page.locator('#evName').fill('Biology 101')
    page.locator('#evColor').fill('#8b5cf6')
    page.locator('#saveEvent').click()
    counts = {}
    for sport in ['baseball', 'mens-basketball', 'womens-volleyball', 'baseball']:
        with page.expect_response(lambda response: '/api/schedule?sport='+sport in response.url, timeout=90000) as result:
            page.locator('#sport').select_option(sport)
        response = result.value
        assert response.status == 200, response.text()
        data = response.json()
        assert data['source'] == 'https://bushnellbeacons.com/sports/'+sport+'/schedule'
        assert data['events'] and data['skipped'] == 0, data
        counts[sport] = len(data['events'])
        page.wait_for_function("document.getElementById('sportStatus').textContent.includes('official competitions loaded')")
        chosen = page.evaluate("""() => {
            const data=JSON.parse(localStorage.getItem('beacon-planner-v1'));
            const sport=document.getElementById('sport').value;
            const events=data.datedEvents.filter(e=>e.sport===sport&&e.status!=='CANCELLED'&&e.status!=='POSTPONED');
            const when=e=>new Date(e.allDay?e.start+'T12:00:00':e.start);
            events.sort((a,b)=>when(a)-when(b));
            return events.find(e=>when(e)>=new Date())||events.at(-1);
        }""")
        assert chosen['title'] in page.locator('#calendarNotes' if chosen['allDay'] else '#calendar').inner_text(), chosen
        if not chosen['allDay']:
            position = page.evaluate('(e)=>{const d=new Date(e.start);return {day:d.getDay(),hour:d.getHours()}}', chosen)
            if position['hour'] >= 8:
                slot = page.locator('.slot[data-day="'+str(position['day'])+'"][data-hour="'+str(position['hour'])+'"] .official-event').filter(has_text=chosen['title'])
                assert slot.count() >= 1, (chosen, position)
        assert 'Biology 101' in page.locator('#calendar').inner_text()
        stored = page.evaluate("JSON.parse(localStorage.getItem('beacon-planner-v1'))")
        assert stored['events'][0]['color'] == '#8b5cf6'
        assert len([e for e in stored['datedEvents'] if e['sport'] == sport]) == counts[sport]
        print('PASS live', sport, counts[sport], 'official competitions; next shown:', chosen['title'], chosen['start'], flush=True)
    page.screenshot(path=str(OUT/'desktop-official.png'), full_page=True)
    page.pdf(path=str(OUT/'official-week.pdf'), prefer_css_page_size=True, print_background=True)
    page.set_viewport_size({'width': 390, 'height': 844})
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    page.screenshot(path=str(OUT/'mobile-official.png'), full_page=True)
    page.locator('.event:not(.official-event)').first.click()
    page.screenshot(path=str(OUT/'class-editor.png'))
    assert not errors, errors
    print('PASS: real competitions render, sport switching preserves classes and colors, repeat selection does not duplicate games; artifacts:', OUT, flush=True)
    browser.close()

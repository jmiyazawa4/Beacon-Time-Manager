"""Run against the production server: BEACON_TEST_URL=http://127.0.0.1:8001 python ..."""
from datetime import datetime,timezone
import os
from playwright.sync_api import sync_playwright
from browser_test_helpers import wait_js
BASE=os.environ.get('BEACON_TEST_URL','http://127.0.0.1:8001')
SECRET='PRIVATE_MARKER_9D'
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
    context=browser.new_context(timezone_id='America/Los_Angeles')
    page=context.new_page();page.clock.install(time=datetime(2026,1,15,20,tzinfo=timezone.utc))
    requests=[]
    context.on('request',lambda r:requests.append((r.method,r.url,r.post_data or '')))
    context.route('**/api/verse',lambda r:r.fulfill(status=502,content_type='application/json',body='{"error":"NIV fixture unavailable"}'))
    context.route('**/api/schedule?*',lambda r:r.fulfill(content_type='application/json',body='{"events":[],"note":"Security fixture"}'))
    response=page.goto(BASE)
    assert "frame-ancestors 'none'" in response.headers['content-security-policy']
    assert response.headers['referrer-policy']=='no-referrer'
    page.locator('#student').fill(SECRET)
    page.locator('#add').click();page.locator('#evName').fill(SECRET);page.locator('#saveEvent').click()
    assert SECRET in page.evaluate("localStorage.getItem('beacon-planner-v1')")
    page.locator('#sport').select_option('baseball')
    wait_js(page,"document.getElementById('sportStatus').textContent.includes('The schedule contains no competitions')")
    attack='<img src="https://attacker.invalid/pixel" onerror="window.privacyAttack=1">'
    ics='BEGIN:VCALENDAR\nBEGIN:VEVENT\nUID:'+SECRET+'\nDTSTART:20260115T200000Z\nSUMMARY:'+attack+'\nEND:VEVENT\nEND:VCALENDAR'
    page.locator('#sportCalendarFile').set_input_files({'name':'private.ics','mimeType':'text/calendar','buffer':ics.encode()})
    wait_js(page,"document.getElementById('sportStatus').textContent.includes('Imported or updated 1')")
    assert page.evaluate('window.privacyAttack') is None
    assert page.locator('img[src*="attacker.invalid"]').count()==0
    assert attack in page.locator('#calendar').inner_text()
    # An arbitrary inline script is rejected by the real production CSP.
    page.evaluate("() => {const s=document.createElement('script');s.textContent='window.cspAttack=1';document.body.append(s)}")
    assert page.evaluate('window.cspAttack') is None
    assert all(SECRET not in url+body for _,url,body in requests),requests
    assert all(method!='POST' and '/api/import' not in url for method,url,_ in requests)
    second=context.new_page();second.goto(BASE)
    assert SECRET in second.locator('#calendar').inner_text()
    page.locator('.privacy-panel summary').click()
    page.once('dialog',lambda d:d.accept());page.locator('#privateSession').check()
    assert page.evaluate("localStorage.getItem('beacon-planner-v1')") is None
    wait_js(second,'BeaconPrivacy.status().privateMode')
    second.locator('#add').click();second.locator('#evName').fill('Other tab private activity');second.locator('#saveEvent').click()
    assert second.evaluate("localStorage.getItem('beacon-planner-v1')") is None
    second.close()
    page.reload();assert page.locator('#privateSession').is_checked()
    assert SECRET not in page.locator('#calendar').inner_text()
    assert page.locator('#student').input_value()==''
    page.evaluate("() => {window.testNotices=[];window.Notification=class {static permission='granted';constructor(title,options){testNotices.push(options.body)}};}")
    page.locator('#reminderText').fill(SECRET);page.locator('#reminderAt').fill('2026-01-14T12:00');page.locator('#addReminder').click()
    page.clock.fast_forward(31000)
    assert page.evaluate('testNotices.length')==1
    assert SECRET not in page.evaluate('testNotices[0]')
    print('PASS: production CSP blocks injected scripts; hostile calendar text stays inert; personal details and calendar files never leave browser; private sessions erase durable planner data and prevent other tabs resaving it; notifications omit sensitive text')
    browser.close()

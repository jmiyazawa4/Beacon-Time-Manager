"""Check the supplied real dates in the application. Start server.py first."""
from datetime import datetime, timezone
from pathlib import Path
import os
from playwright.sync_api import sync_playwright
from browser_test_helpers import wait_js

OUT = Path('/tmp/beacon-academic-check')
OUT.mkdir(exist_ok=True)
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
    page=browser.new_page(timezone_id='America/Los_Angeles',viewport={'width':1440,'height':1000},accept_downloads=True)
    page.clock.install(time=datetime(2026,11,26,20,tzinfo=timezone.utc))
    page.route('**/schedules/*.json',lambda r:r.fulfill(status=502,content_type='application/json',body='{"error":"Sports service fixture"}'))
    page.goto(os.environ.get('BEACON_TEST_URL','http://127.0.0.1:8000'))
    wait_js(page,"BeaconAcademic.status().verified")
    assert page.locator('.slot[data-day="4"].academic-holiday').count()==16
    assert page.locator('.slot[data-day="5"].academic-holiday').count()==16
    assert page.locator('.slot[data-day="6"].academic-holiday').count()==0
    assert 'Thanksgiving Holiday' not in page.locator('#calendarNotes').inner_text()
    if page.locator('.academic-banner').get_attribute('open') is None:page.locator('.academic-banner summary').click()
    assert 'Thanksgiving Holiday' in page.locator('#academicWeekList').inner_text()
    page.locator('#sport').select_option('baseball')
    wait_js(page,"document.getElementById('sportStatus').textContent.includes('Sports service')")
    assert 'Thanksgiving Holiday' not in page.locator('#calendarNotes').inner_text()
    if page.locator('.academic-banner').get_attribute('open') is None:page.locator('.academic-banner summary').click()
    assert 'Thanksgiving Holiday' in page.locator('#academicWeekList').inner_text()
    page.locator('#sport').select_option('softball')
    assert page.locator('.slot[data-day="4"].academic-holiday').count()==16
    page.locator('#print').click()
    page.locator('input[name="pdfLayout"][value="agenda"]').check()
    with page.expect_download() as result:page.locator('#exportDownload').click()
    result.value.save_as(OUT/'thanksgiving-week.pdf')
    page.keyboard.press('Escape')
    for _ in range(17):page.locator('#nextWeek').click()
    assert 'Mar 21' in page.locator('#weekLabel').inner_text()
    assert page.locator('.slot[data-day="1"].academic-break').count()==16
    assert page.locator('.slot[data-day="5"].academic-holiday').count()==16
    assert page.locator('.slot[data-day="6"].academic-break').count()==16
    page.locator('#nextWeek').click()
    assert page.locator('.slot[data-day="0"].academic-break').count()==16
    assert page.locator('.slot[data-day="1"].academic-break').count()==0
    page.locator('#prevWeek').click()
    page.screenshot(path=str(OUT/'spring-break.png'),full_page=True)
    print('PASS: real Thanksgiving and spring-break boundaries, Good Friday priority, holidays across sports, and academic PDF download')
    browser.close()

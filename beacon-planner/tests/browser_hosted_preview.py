"""Check the static review page with no APIs and enforced private-session mode."""
from datetime import datetime,timezone
from pathlib import Path
from playwright.sync_api import sync_playwright
from browser_test_helpers import wait_js
HTML=Path('/workspace/artifacts/beacon-hosted-preview/index.html')
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
 page=b.new_page(viewport={'width':1440,'height':1000},timezone_id='America/Los_Angeles',accept_downloads=True)
 page.clock.install(time=datetime(2027,1,20,20,tzinfo=timezone.utc))
 requested=[];page.on('request',lambda r:requested.append(r.url))
 url='https://beacon-preview.invalid/'
 page.route('**/*',lambda r:r.fulfill(content_type='text/html',body=HTML.read_text()) if r.request.url==url else r.abort())
 page.goto(url);wait_js(page,'BeaconAcademic.status().verified');wait_js(page,"BeaconVerses.current() !== null")
 assert page.evaluate('BeaconVerses.current().translation')=='KJV'
 assert page.locator('#readingPassages a').count()==4
 assert page.locator('#privateSession').is_checked() and page.locator('#privateSession').is_disabled()
 assert page.locator('.view-buttons').count()==0
 page.locator('#add').click();page.locator('#evName').fill('Example review class');page.locator('#saveEvent').click()
 assert 'Example review class' in page.locator('#calendar').inner_text()
 assert page.evaluate("localStorage.getItem('beacon-planner-v1')") is None
 page.locator('#sport').select_option('baseball');wait_js(page,"document.getElementById('sportStatus').textContent.includes('57 official competitions')")
 page.locator('#print').click()
 with page.expect_download() as pdf:page.locator('#exportDownload').click()
 assert pdf.value.suggested_filename.endswith('.pdf')
 page.keyboard.press('Escape')
 page.evaluate("() => {const s=document.createElement('script');s.textContent='window.unsafePreview=1';document.body.append(s)}")
 assert page.evaluate('window.unsafePreview') is None
 page.reload();assert 'Example review class' not in page.locator('#calendar').inner_text()
 assert all(request==url for request in requested),requested
 print('PASS: static preview supports editing, real saved sports data, academic dates and PDF downloads without APIs; private mode is mandatory; no saved planner data; CSP rejects injected scripts')
 b.close()

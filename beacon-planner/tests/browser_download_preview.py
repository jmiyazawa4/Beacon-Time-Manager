"""Validate a built single-file preview without requesting the development server."""
from pathlib import Path
from playwright.sync_api import sync_playwright
from browser_test_helpers import wait_js
import os

HTML = Path(os.environ.get('BEACON_PREVIEW_HTML','/workspace/artifacts/beacon-browser-review/Beacon-Time-Manager.html'))
OUT = HTML.parent
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
    page=browser.new_page(viewport={'width':1440,'height':1000},timezone_id='America/Los_Angeles',accept_downloads=True)
    errors=[];requests=[]
    page.on('pageerror',lambda error:errors.append(str(error)))
    page.on('request',lambda request:requests.append(request.url))
    url='https://beacon-preview.invalid/Beacon-Time-Manager.html'
    page.route('**/*',lambda route:route.fulfill(content_type='text/html',body=HTML.read_text()) if route.request.url==url else route.abort())
    page.goto(url)
    wait_js(page,'BeaconAcademic.status().verified')
    assert page.locator('.preview-notice').is_visible()
    assert page.evaluate("getComputedStyle(document.body).backgroundColor")=='rgb(246, 242, 233)'
    assert 'Georgia' in page.locator('.hero h2').evaluate('(e)=>getComputedStyle(e).fontFamily')
    calendar=page.locator('.calendar-wrap').bounding_box();academic=page.locator('.academic-banner').bounding_box()
    assert academic['y'] >= calendar['y']+calendar['height']
    page.locator('#add').click();page.locator('#evName').fill('Independent exploration test');page.locator('#evColor').fill('#9b7429');page.locator('#saveEvent').click()
    assert 'Independent exploration test' in page.locator('#calendar').inner_text()
    page.reload();assert 'Independent exploration test' in page.locator('#calendar').inner_text()
    for sport,count in [('baseball',57),('mens-basketball',37),('womens-volleyball',35)]:
        page.locator('#sport').select_option(sport)
        wait_js(page,"document.getElementById('sportStatus').textContent.includes('official competitions loaded')")
        state=page.evaluate("JSON.parse(localStorage.getItem('beacon-planner-v1'))")
        assert len([e for e in state['datedEvents'] if e['sport']==sport])==count
        assert len(state['events'])==1
    page.locator('#print').click();page.locator('input[name="pdfLayout"][value="agenda"]').check()
    with page.expect_download() as result:page.locator('#exportDownload').click()
    result.value.save_as(OUT/'preview-test-export.pdf')
    page.keyboard.press('Escape')
    assert not errors,errors
    assert all(request==url for request in requests),requests
    page.screenshot(path=str(OUT/'design-b-current.png'),full_page=True)
    page.set_viewport_size({'width':390,'height':844})
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    print('PASS: standalone preview has no API or asset network requests, uses design B, academic panel is below calendar, edits persist, three official snapshots load, PDF downloads, mobile fits')
    browser.close()

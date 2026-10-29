"""Optional UI, daily verse, and generated-PDF checks. Start server.py first."""
from datetime import datetime, timezone
from pathlib import Path
import os
import json
from playwright.sync_api import sync_playwright

OUT = Path(os.environ.get('BEACON_TEST_ARTIFACTS', '/tmp/beacon-feature-check'))
OUT.mkdir(parents=True, exist_ok=True)
with sync_playwright() as p:
    browser = p.chromium.launch(executable_path='/usr/bin/chromium', headless=True, args=['--no-sandbox'])
    page = browser.new_page(viewport={'width': 1440, 'height': 1000}, timezone_id='America/Los_Angeles', accept_downloads=True)
    page.clock.install(time=datetime(2026, 1, 15, 20, tzinfo=timezone.utc))
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    niv_calls = []
    def niv_fixture(route):
        niv_calls.append(route.request.url)
        payload = {'text':'NIV preview placeholder. The live passage is supplied by Bible Gateway.', 'reference':'NIV service preview '+str(len(niv_calls)), 'copyright':'Test fixture attribution. This preview is not Scripture.', 'translation':'NIV', 'link':'https://www.biblegateway.com/'}
        route.fulfill(content_type='application/json', body=json.dumps(payload))
    page.route('**/api/verse', niv_fixture)
    academic_fixture={'verified':True,'program':'Test fixture calendar (not official dates)','academicYear':'2025-26 fixture','source':'https://bushnell.edu/academics/academic-calendars/','events':[{'id':'academic-fixture-holiday','title':'Fixture university holiday','start':'2026-01-12','end':'2026-01-13','kind':'holiday'},{'id':'academic-fixture-break','title':'Fixture university break','start':'2026-01-14','end':'2026-01-17','kind':'break'}]}
    page.route('**/academic-calendar.json',lambda route:route.fulfill(content_type='application/json',body=json.dumps(academic_fixture)))
    page.route('**/api/schedule?*', lambda route: route.fulfill(status=502, content_type='application/json', body='{"error":"Fixture: live schedule unavailable"}'))
    page.add_init_script("""if(!localStorage.getItem('beacon-planner-v1')) localStorage.setItem('beacon-planner-v1',JSON.stringify({student:'Sample student',sport:'baseball',datedEvents:[{key:'baseball|fixture',sport:'baseball',title:'Fixture official competition',start:'2026-01-15T12:30:00-08:00',end:null,allDay:false,location:'Fixture gym',source:'Official Bushnell schedule'},{key:'baseball|tba',sport:'baseball',title:'Fixture TBA competition',start:'2026-01-16',end:'2026-01-17',allDay:true,timeUnknown:true,timeLabel:'Time TBA',source:'Official Bushnell schedule'}],goals:[{id:'g',text:'Complete biology lab',done:false}],reminders:[],events:[{id:'class',name:'Biology 101 - laboratory and discussion',cat:'Class',start:540,end:660,days:[1,3,5],color:'#8b5cf6'},{id:'practice',name:'Team practice',cat:'Practice',start:900,end:1020,days:[1,2,3,4,5],color:'#f6c642'},{id:'chapel',name:'Chapel',cat:'Chapel',start:600,end:660,days:[2],color:'#477dbb'},{id:'work',name:'Campus work',cat:'Work',start:780,end:960,days:[0,6],color:'#2d8b76'}]}));""")
    page.goto(os.environ.get('BEACON_TEST_URL', 'http://127.0.0.1:8000'))
    page.wait_for_function("document.getElementById('verseReference').textContent.includes('NIV service preview')")
    assert page.locator('#verseText').inner_text()
    assert 'NIV' in page.locator('#verseReference').inner_text()
    assert 'Test fixture attribution' in page.locator('#verseCopyright').inner_text()
    assert 'January 15, 2026' in page.locator('#verseDate').inner_text()
    assert page.evaluate('BeaconVerses.current().translation') == 'NIV'
    page.wait_for_function("document.getElementById('academicStatus').textContent.includes('Test fixture calendar')")
    assert page.locator('.layout > .panel > .academic-banner').count() == 1
    assert page.locator('.academic-banner').evaluate("e=>!!(document.querySelector('.calendar-wrap').compareDocumentPosition(e)&Node.DOCUMENT_POSITION_FOLLOWING)")
    assert page.locator('.slot[data-day="1"].academic-holiday').count() == 16
    assert page.locator('.slot[data-day="3"].academic-break').count() == 16
    assert 'Fixture university holiday' in page.locator('#calendarNotes').inner_text()
    page.locator('#sport').select_option('softball')
    page.wait_for_function("document.getElementById('sportStatus').textContent.includes('Fixture:')")
    assert page.locator('.slot[data-day="1"].academic-holiday').count() == 16
    assert 'Fixture university holiday' in page.locator('#calendarNotes').inner_text()
    page.locator('#sport').select_option('baseball')
    before = len(niv_calls)
    page.evaluate('BeaconVerses.load()')
    assert len(niv_calls) == before
    # Legacy saved view preferences must not restore a student-facing switcher.
    page.evaluate("localStorage.setItem('beacon-planner-view','agenda')")
    page.reload()
    page.wait_for_function("BeaconAcademic.status().verified")
    assert page.locator('.website-views').count() == 0
    assert page.locator('.view-buttons').count() == 0
    assert page.locator('body').get_attribute('data-planner-view') == 'dashboard'
    assert page.locator('.dashboard-agenda-card').is_visible()
    assert not page.locator('#hoursSummaryCard').is_visible()
    assert 'Scheduled hours' not in page.locator('.sidebar').inner_text()
    assert page.locator('.calendar-wrap').is_visible()
    page.locator('#agendaDays button').nth(1).click()
    assert 'Biology 101' in page.locator('.dashboard-agenda-card').inner_text()
    assert 'Fixture university holiday' in page.locator('.dashboard-agenda-card').inner_text()
    page.locator('.dashboard-agenda-card .agenda-event').filter(has_text='Biology 101').click()
    page.locator('#evName').fill('Updated biology class')
    page.locator('#evColor').fill('#d946ef')
    page.locator('#saveEvent').click()
    assert 'Updated biology class' in page.locator('#agendaEvents').inner_text()
    page.locator('#nextWeek').click()
    assert 'January 19, 2026' in page.locator('#agendaDate').inner_text()
    page.locator('#prevWeek').click()
    page.screenshot(path=str(OUT/'dashboard-desktop.png'), full_page=True)
    for width in (375,390,768):
        page.set_viewport_size({'width':width,'height':844})
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'),width
    page.set_viewport_size({'width':390,'height':844})
    page.screenshot(path=str(OUT/'dashboard-mobile.png'),full_page=True)
    page.set_viewport_size({'width':1440,'height':1000})
    page.locator('#print').click()
    assert page.locator('#exportDialog').is_visible()
    for layout in ['grid', 'agenda', 'daily']:
        page.locator('input[name="pdfLayout"][value="'+layout+'"]').check()
        page.locator('#exportVerse').check()
        with page.expect_download() as result:
            page.locator('#exportDownload').click()
        download = result.value
        assert download.suggested_filename.endswith('-'+layout+'.pdf')
        download.save_as(OUT/(layout+'.pdf'))
        assert not page.locator('#exportError').inner_text()
    with page.expect_popup() as preview:
        page.locator('#exportPreview').click()
    assert preview.value.url.startswith('blob:')
    preview.value.close()
    page.locator('#exportPaper').select_option('a4')
    page.locator('#exportGrayscale').check()
    page.locator('input[name="pdfLayout"][value="grid"]').check()
    with page.expect_download() as result:
        page.locator('#exportDownload').click()
    result.value.save_as(OUT/'grid-a4-grayscale.pdf')
    page.set_viewport_size({'width': 390, 'height': 844})
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    page.screenshot(path=str(OUT/'export-options.png'))
    page.keyboard.press('Escape')
    assert not page.locator('#exportDialog').is_visible()
    old = page.locator('#verseReference').inner_text()
    page.clock.fast_forward(86400000)
    page.wait_for_function("document.getElementById('verseReference').textContent !== "+json.dumps(old))
    assert page.locator('#verseReference').inner_text() != old
    assert 'January 16, 2026' in page.locator('#verseDate').inner_text()
    assert not errors, errors
    failed = browser.new_page()
    failed.route('**/api/verse', lambda route: route.fulfill(status=502, content_type='application/json', body='{"error":"Unable to load the NIV verse"}'))
    failed.goto(os.environ.get('BEACON_TEST_URL', 'http://127.0.0.1:8000'))
    failed.wait_for_function("document.getElementById('verseStatus').textContent.includes('Unable to load')")
    assert not failed.locator('#verseText').is_visible()
    assert 'NIV' in failed.locator('#verseReference').inner_text()
    assert 'KJV' not in failed.locator('.daily-verse-card').inner_text()
    failed.locator('#print').click()
    failed.locator('#exportVerse').check()
    failed.locator('#exportDownload').click()
    assert 'NIV verse has not loaded' in failed.locator('#exportError').inner_text()
    failed.close()
    print('PASS: shared academic fixtures across sports and holiday/break shading; one student dashboard without a view switcher; daily-agenda class/color editing; mobile widths; NIV provider payload/attribution, daily refresh, and unavailable-service behavior; three downloadable PDF layouts; A4/grayscale; dialog dismissal; no JS errors')
    print('Artifacts:', OUT)
    browser.close()

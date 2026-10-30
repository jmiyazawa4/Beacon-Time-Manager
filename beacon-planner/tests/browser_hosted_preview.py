"""Check the static review page with no APIs, browser saving, and optional private sessions."""
from datetime import datetime,timezone
from pathlib import Path
from playwright.sync_api import sync_playwright
from browser_test_helpers import wait_js
HTML=Path('/workspace/artifacts/beacon-hosted-preview/index.html')
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
 context=b.new_context(viewport={'width':1440,'height':1000},timezone_id='America/Los_Angeles',accept_downloads=True)
 page=context.new_page()
 page.clock.install(time=datetime(2027,1,20,20,tzinfo=timezone.utc))
 requested=[];page.on('request',lambda r:requested.append(r.url))
 url='https://beacon-preview.invalid/'
 page.context.route('**/*',lambda r:r.fulfill(content_type='text/html',body=HTML.read_text()) if r.request.url==url else r.abort())
 page.goto(url);wait_js(page,'BeaconAcademic.status().verified');wait_js(page,"BeaconVerses.current() !== null")
 assert page.evaluate('BeaconVerses.current().translation')=='KJV'
 assert page.locator('#readingPassages a').count()==4
 assert page.evaluate('BeaconPlanner.getSchedule().days.some(d=>d.events.some(e=>e.academic))')
 page.locator('#showAcademic').uncheck()
 assert page.evaluate('BeaconPlanner.getSchedule().days.every(d=>d.events.every(e=>!e.academic))&&BeaconPlanner.getSchedule().days.some(d=>d.holiday==="holiday")')
 page.reload();wait_js(page,'BeaconAcademic.status().verified')
 assert not page.locator('#showAcademic').is_checked()
 assert page.evaluate('BeaconPlanner.getSchedule().days.every(d=>d.events.every(e=>!e.academic))')
 page.locator('#showAcademic').check()
 assert page.evaluate('BeaconPlanner.getSchedule().days.some(d=>d.events.some(e=>e.academic))')
 assert not page.locator('#privateSession').is_checked() and not page.locator('#privateSession').is_disabled()
 assert page.locator('.view-buttons').count()==0
 page.locator('#add').click();page.locator('#evName').fill('Example review class');page.locator('#saveEvent').click()
 assert 'Example review class' in page.locator('#calendar').inner_text()
 assert page.evaluate("JSON.parse(localStorage.getItem('beacon-planner-v1')).events[0].name")=='Example review class'
 page.locator('#goalInput').fill('Example goal');page.locator('#addGoal').click()
 page.locator('#reminderText').fill('Example reminder');page.locator('#reminderAt').fill('2027-01-21T10:00');page.locator('#addReminder').click()
 page.reload()
 assert 'Example review class' in page.locator('#calendar').inner_text()
 assert 'Example goal' in page.locator('#goals').inner_text()
 assert 'Example reminder' in page.locator('#reminders').inner_text()
 context=page.context;page.close();page=context.new_page()
 page.clock.install(time=datetime(2027,1,20,20,tzinfo=timezone.utc))
 page.on('request',lambda r:requested.append(r.url))
 page.goto(url)
 assert 'Example review class' in page.locator('#calendar').inner_text()
 assert 'Example goal' in page.locator('#goals').inner_text()
 page.locator('#sport').select_option('baseball');wait_js(page,"document.getElementById('sportStatus').textContent.includes('57 official competitions')")
 page.locator('#print').click()
 with page.expect_download() as pdf:page.locator('#exportDownload').click()
 assert pdf.value.suggested_filename.endswith('.pdf')
 page.keyboard.press('Escape')
 page.evaluate("() => {const s=document.createElement('script');s.textContent='window.unsafePreview=1';document.body.append(s)}")
 assert page.evaluate('window.unsafePreview') is None
 page.on('dialog',lambda d:d.accept())
 page.locator('details.privacy-panel').evaluate('(e)=>e.open=true')
 page.locator('#privateSession').check()
 assert page.evaluate("localStorage.getItem('beacon-planner-v1')") is None
 page.reload();assert 'Example review class' not in page.locator('#calendar').inner_text()
 assert page.locator('#privateSession').is_checked()
 page.locator('details.privacy-panel').evaluate('(e)=>e.open=true')
 page.locator('#privateSession').uncheck()
 page.locator('#add').click();page.locator('#evName').fill('Erase this class');page.locator('#saveEvent').click()
 page.locator('#reset').click();page.reload()
 assert 'Erase this class' not in page.locator('#calendar').inner_text()
 page.locator('#sport').select_option('baseball')
 wait_js(page,"document.getElementById('sportStatus').textContent.includes('official competitions')")
 page.locator('details.sport-options').evaluate('(e)=>e.open=true')
 assert page.locator('#csvScheduleFile').get_attribute('accept') is None
 csv=b'Date,Event,Duration,Location,Required Attendance,Description\n2027-01-20,Synthetic CSV Practice,3:30-5:40pm,Field,Tuesday Group,CSV example\n2027-01-20,Synthetic CSV Meeting,TBD,Campus,All,Confirm time'
 for repeat in range(2):
  with page.expect_file_chooser() as picker:page.locator('#importCSV').click()
  picker.value.set_files({'name':'example.csv','mimeType':'text/csv','buffer':csv})
  wait_js(page,"document.getElementById('sportStatus').textContent.includes('Imported or updated 2')")
 stored=page.evaluate("JSON.parse(localStorage.getItem('beacon-planner-v1'))")
 imported=[e for e in stored['datedEvents'] if e['title'].startswith('Synthetic CSV')]
 assert len(imported)==2
 known=next(e for e in imported if e['title']=='Synthetic CSV Practice')
 assert known['category']=='Practice' and known['attendance']=='Tuesday Group'
 page.locator('#currentWeek').click()
 assert page.locator('.event').filter(has_text='Synthetic CSV Practice').count()==1
 assert 'Synthetic CSV Meeting' in page.locator('#calendarNotes').inner_text()
 assert page.locator('.help-title').filter(has_text='Counselor Coordinator').count()==1
 assert page.locator('.help-contact strong').filter(has_text='Tutoring Center').count()==1
 assert page.locator('a[href="mailto:tutoring@bushnell.edu"]').count()==1
 assert page.locator('a[href="https://my.bushnell.edu/ICS/Campus_Life/Tutoring.jnz"]').count()==1
 assert page.locator('a[href*="christi-cameron"]').count()==0

 assert all(request==url for request in requested),requested
 print('PASS: static preview supports editing, real saved sports data, academic dates and PDF downloads without APIs; browser entries survive reload; optional private mode erases saved entries; Clear all clears the planner; CSP rejects injected scripts')
 b.close()

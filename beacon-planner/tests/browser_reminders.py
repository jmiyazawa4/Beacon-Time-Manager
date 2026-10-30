"""Importance/color edits persist; old reminders keep safe defaults and private mode stays local."""
from pathlib import Path
from datetime import datetime,timezone
from playwright.sync_api import sync_playwright
HTML=Path('/workspace/artifacts/beacon-hosted-preview/index.html')
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
 page=b.new_page(viewport={'width':1440,'height':1000},timezone_id='America/Los_Angeles')
 page.clock.install(time=datetime(2026,10,30,20,tzinfo=timezone.utc))
 url='https://beacon-preview.invalid/';requests=[];page.on('request',lambda r:requests.append(r.url))
 page.route('**/*',lambda r:r.fulfill(content_type='text/html',body=HTML.read_text()) if r.request.url==url else r.abort())
 page.goto(url)
 page.locator('#reminderText').fill('Example assignment');page.locator('#reminderAt').fill('2026-11-02T09:00')
 page.locator('#reminderPriority').select_option('high');page.locator('#reminderColor').fill('#e11d48');page.locator('#addReminder').click()
 row=page.locator('.reminder-item');assert row.count()==1 and 'High importance' in row.inner_text()
 assert row.evaluate('(e)=>e.style.borderLeftColor')=='rgb(225, 29, 72)'
 original=page.evaluate("JSON.parse(localStorage.getItem('beacon-planner-v1')).reminders[0]")
 page.reload();assert 'High importance' in page.locator('.reminder-item').inner_text()
 page.locator('.edit-reminder').click();page.locator('#reminderPriority').select_option('low');page.locator('#reminderColor').fill('#17834f');page.locator('#reminderText').fill('Updated assignment');page.locator('#addReminder').click()
 saved=page.evaluate("JSON.parse(localStorage.getItem('beacon-planner-v1')).reminders")
 assert len(saved)==1 and saved[0]['id']==original['id'] and saved[0]['priority']=='low' and saved[0]['color']=='#17834f'
 page.locator('.edit-reminder').click();page.locator('#reminderPriority').select_option('high');page.locator('#cancelReminderEdit').click()
 assert 'Low importance' in page.locator('.reminder-item').inner_text()
 page.evaluate("() => {const s=JSON.parse(localStorage.getItem('beacon-planner-v1'));delete s.reminders[0].priority;delete s.reminders[0].color;localStorage.setItem('beacon-planner-v1',JSON.stringify(s));}")
 page.reload();assert 'Normal importance' in page.locator('.reminder-item').inner_text()
 for width in [390,768,1440]:
  page.set_viewport_size({'width':width,'height':1000});assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),width
 page.locator('.delete-reminder').click();assert page.locator('.reminder-item').count()==0
 assert all(r==url for r in requests),requests
 print('PASS: reminder importance/custom colors, editing without duplication, persistence, cancel, legacy defaults, deletion, responsive widths and no uploads')
 b.close()

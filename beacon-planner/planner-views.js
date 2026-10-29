(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const planner = window.BeaconPlanner;
  $('stats').closest('section').classList.add('time-summary-card');
  $('goals').closest('section').classList.add('goals-card');
  $('reminders').closest('section').classList.add('reminders-card');
  const names = {dashboard: 'Dashboard', calendar: 'Calendar focus', agenda: 'Daily agenda'};
  const store = (key, value) => {try {localStorage.setItem(key, value);} catch {}};
  const read = (key, fallback) => {try {return localStorage.getItem(key) || fallback;} catch {return fallback;}};
  const controls = document.createElement('div');
  controls.className = 'website-views no-print';
  controls.innerHTML = `<div><strong>Planner view</strong><span>Choose a layout for your week.</span></div><div class="view-buttons" role="group" aria-label="Planner layout">${Object.entries(names).map(([key, name]) => `<button type="button" data-view="${key}" aria-pressed="false"><i class="view-icon icon-${key}" aria-hidden="true"></i>${name}</button>`).join('')}</div>`;
  document.querySelector('main.wrap').prepend(controls);
  const agenda = document.createElement('div');
  agenda.id = 'agendaView'; agenda.className = 'agenda-view';
  agenda.innerHTML = '<nav id="agendaDays" class="agenda-days" aria-label="Choose an agenda day"></nav><div class="agenda-heading"><div><span class="section-index">DAILY SCHEDULE</span><h3 id="agendaDate"></h3></div><button id="agendaAdd" type="button">+ Add activity</button></div><div id="agendaEvents" class="agenda-events"></div>';
  document.querySelector('.calendar-wrap').before(agenda);
  let selectedDay = new Date().getDay();
  function formatTime(minutes) {
    const m = minutes % 1440, h = Math.floor(m / 60);
    return `${h % 12 || 12}:${String(m % 60).padStart(2, '0')} ${h < 12 ? 'AM' : 'PM'}`;
  }
  function renderAgenda() {
    const schedule = planner.getSchedule();
    $('agendaDays').replaceChildren();
    schedule.days.forEach(day => {
      const button = document.createElement('button'); button.type = 'button'; button.setAttribute('aria-pressed', String(day.index === selectedDay));
      const label = document.createElement('strong'); label.textContent = day.shortLabel;
      const count = document.createElement('span'); count.textContent = day.events.length + (day.events.length === 1 ? ' activity' : ' activities');
      button.append(label, count); button.onclick = () => {selectedDay = day.index; renderAgenda();}; $('agendaDays').append(button);
    });
    const day = schedule.days[selectedDay]; $('agendaDate').textContent = day.label;
    $('agendaEvents').replaceChildren();
    if (!day.events.length) {
      const empty = document.createElement('div'); empty.className = 'agenda-empty';
      const title = document.createElement('h4'); title.textContent = 'No activities scheduled';
      const detail = document.createElement('p'); detail.textContent = 'Add a class or personal activity for this day.';
      empty.append(title, detail); $('agendaEvents').append(empty);
    }
    day.events.forEach(event => {
      const button = document.createElement('button'); button.type = 'button'; button.className = 'agenda-event'; button.style.setProperty('--event-color', event.color);
      const time = document.createElement('span'); time.className = 'agenda-event-time'; time.textContent = event.allDay ? (event.timeUnknown ? event.timeLabel || 'Time TBA' : 'All day') : formatTime(event.start);
      if (!event.allDay && event.endKnown) {const end = document.createElement('small'); end.textContent = 'to ' + formatTime(event.end); time.append(end);}
      const body = document.createElement('span'); body.className = 'agenda-event-body';
      const title = document.createElement('strong'); title.textContent = event.title;
      const detail = document.createElement('small'); detail.textContent = [event.category, event.location].filter(Boolean).join(' · ');
      body.append(title, detail);
      const action = document.createElement('span'); action.className = 'agenda-event-action'; action.textContent = event.personal ? 'Edit activity' : event.academic ? 'University calendar' : 'Official schedule';
      button.append(time, body, action); button.onclick = () => planner.editActivity(event.id); $('agendaEvents').append(button);
    });
  }
  $('agendaAdd').onclick = () => planner.addActivity(selectedDay);
  function setView(view) {
    const safe = names[view] ? view : 'dashboard';
    document.body.dataset.plannerView = safe; store('beacon-planner-view', safe);
    document.querySelector('.section-heading h2').textContent = safe === 'agenda' ? 'Daily agenda' : 'Weekly calendar';
    document.querySelector('.layout > .panel > .sub').textContent = safe === 'agenda' ? 'Select a day. Click an activity to edit its name, time, days, or color.' : 'Click an empty time to add a class or activity. Click a block to edit its name, time, days, or color.';
    controls.querySelectorAll('[data-view]').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.view === safe)));
    renderAgenda();
  }
  controls.querySelectorAll('[data-view]').forEach(button => button.onclick = () => setView(button.dataset.view));
  document.addEventListener('beacon:render', renderAgenda);
  setView(read('beacon-planner-view', 'dashboard'));

  const academicBanner = document.createElement('div');
  academicBanner.className = 'academic-banner no-print';
  academicBanner.innerHTML = '<div><strong>University calendar</strong><span id="academicStatus" role="status">Loading academic dates…</span></div><a href="https://bushnell.edu/academics/academic-calendars/" target="_blank" rel="noopener">Official academic calendars ↗</a>';
  document.querySelector('.sport-panel').after(academicBanner);
  function renderAcademicStatus() {
    const data=window.BeaconAcademic.status();
    $('academicStatus').textContent=data.verified?[data.program,data.academicYear,'Shared across sports. Check course-session labels; holidays and breaks are shaded.'].filter(Boolean).join(' · '):data.error||'University academic dates are not available yet.';
  }
  document.addEventListener('beacon:academic',renderAcademicStatus);
  window.BeaconAcademic.load();

  const verseCard = document.createElement('section'); verseCard.className = 'daily-verse-card';
  verseCard.innerHTML = '<span class="section-index">SCRIPTURE · NIV</span><h2>Verse of the day</h2><time id="verseDate"></time><blockquote id="verseText"></blockquote><a id="verseReference" target="_blank" rel="noopener"></a><p class="verse-note" id="verseCopyright"></p><p class="verse-note" id="verseStatus" role="status"></p><button class="verse-retry" id="verseRetry" type="button">Retry NIV verse</button>';
  document.querySelector('.sidebar').prepend(verseCard);
  function renderVerse() {
    const verse = window.BeaconVerses.current(), status = window.BeaconVerses.status();
    $('verseDate').textContent = verse?.date || new Date().toLocaleDateString('en-US', {month:'long', day:'numeric', year:'numeric'});
    $('verseText').textContent = verse?.text || '';
    $('verseText').hidden = !verse;
    $('verseReference').textContent = verse ? verse.reference + ' · NIV' : 'Read the NIV verse on Bible Gateway';
    $('verseReference').href = verse?.link || 'https://www.biblegateway.com/reading-plans/verse-of-the-day/next?version=NIV';
    $('verseCopyright').textContent = verse?.copyright || '';
    $('verseStatus').textContent = verse ? 'Daily selection from Bible Gateway' : status.state === 'loading' ? 'Loading today’s NIV verse…' : status.error || 'The NIV verse requires an internet connection.';
    $('verseRetry').hidden = status.state !== 'error';
  }
  function updateVerse() {renderVerse(); window.BeaconVerses.load().then(renderVerse);}
  document.addEventListener('beacon:verse', renderVerse);
  $('verseRetry').onclick = () => window.BeaconVerses.load(true).then(renderVerse);
  let lastDay = window.BeaconVerses.dayKey();
  setInterval(() => {if (window.BeaconVerses.dayKey() !== lastDay) {lastDay = window.BeaconVerses.dayKey(); updateVerse();}}, 60000);
  window.addEventListener('focus', () => {if (window.BeaconVerses.dayKey() !== lastDay) {lastDay = window.BeaconVerses.dayKey(); updateVerse();}});
  document.addEventListener('visibilitychange', () => {if (!document.hidden && window.BeaconVerses.dayKey() !== lastDay) {lastDay = window.BeaconVerses.dayKey(); updateVerse();}});
  updateVerse();

  const modal = document.createElement('div'); modal.className = 'modal'; modal.id = 'exportDialog';
  modal.setAttribute('role', 'dialog'); modal.setAttribute('aria-modal', 'true'); modal.setAttribute('aria-labelledby', 'exportTitle');
  modal.innerHTML = `<div class="dialog export-dialog"><span class="section-index">SCHEDULE DOWNLOAD</span><h2 id="exportTitle">Print or download your schedule</h2><p class="sub">Export the week currently displayed, including personal activities and loaded competitions.</p><fieldset class="export-layouts"><legend>Choose a print layout</legend>
    <label><input type="radio" name="pdfLayout" value="grid" checked><span class="layout-thumbnail thumb-grid" aria-hidden="true"></span><strong>Weekly grid</strong><small>One landscape page. Compact blocks; long titles may shorten.</small></label>
    <label><input type="radio" name="pdfLayout" value="agenda"><span class="layout-thumbnail thumb-agenda" aria-hidden="true"></span><strong>Weekly agenda</strong><small>Portrait day lists with full activity names and locations.</small></label>
    <label><input type="radio" name="pdfLayout" value="daily"><span class="layout-thumbnail thumb-daily" aria-hidden="true"></span><strong>Daily pages</strong><small>A portrait page for each day, with space for written notes.</small></label>
    </fieldset><div class="export-options"><label>Paper size<select id="exportPaper"><option value="letter">US Letter</option><option value="a4">A4</option></select></label><label class="check-option"><input type="checkbox" id="exportGrayscale">Grayscale</label><label class="check-option"><input type="checkbox" id="exportVerse">Include today’s verse</label></div><p class="sub">PDFs are created on your device. Dense agendas can continue onto additional pages.</p><div class="error" id="exportError" role="status"></div><div class="actions"><button class="secondary" id="exportCancel">Cancel</button><button class="secondary" id="exportPreview">Preview / Print</button><button id="exportDownload">Download PDF</button></div></div>`;
  document.body.append(modal);
  let opener;
  const close = () => {modal.classList.remove('show'); opener?.focus();};
  $('print').onclick = () => {opener = document.activeElement; $('exportError').textContent = ''; modal.classList.add('show'); modal.querySelector('input:checked').focus();};
  $('exportCancel').onclick = close;
  modal.onclick = event => {if (event.target === modal) close();};
  modal.addEventListener('keydown', event => {
    if (event.key === 'Escape') {event.preventDefault(); close();}
    if (event.key === 'Tab') {
      const items = [...modal.querySelectorAll('button,input,select')].filter(e => !e.disabled);
      if (event.shiftKey && document.activeElement === items[0]) {event.preventDefault(); items.at(-1).focus();}
      else if (!event.shiftKey && document.activeElement === items.at(-1)) {event.preventDefault(); items[0].focus();}
    }
  });
  function exportPDF(preview) {
    try {
      const schedule = planner.getSchedule();
      const options = {layout: modal.querySelector('input[name="pdfLayout"]:checked').value, paper: $('exportPaper').value, grayscale: $('exportGrayscale').checked, includeVerse: $('exportVerse').checked};
      if (options.includeVerse && !schedule.verse) throw Error('Today’s NIV verse has not loaded. Retry it or uncheck Include today’s verse.');
      const doc = window.BeaconPDF.build(schedule, options);
      if (preview) {
        const url = URL.createObjectURL(doc.output('blob'));
        const tab = window.open(url, '_blank');
        if (!tab) {URL.revokeObjectURL(url); throw Error('Allow this preview to open, or use Download PDF.');}
        tab.opener = null; setTimeout(() => URL.revokeObjectURL(url), 60000);
      } else doc.save(`Beacon-schedule-${schedule.weekKey}-${options.layout}.pdf`);
      $('exportError').textContent = '';
    } catch (error) {$('exportError').textContent = error.message || 'Unable to create the PDF.';}
  }
  $('exportDownload').onclick = () => exportPDF(false);
  $('exportPreview').onclick = () => exportPDF(true);
})();

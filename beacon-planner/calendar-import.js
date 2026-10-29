/* Calendar files are parsed on the device, never uploaded to the server. */
(() => {
  'use strict';
  const MAX_BYTES = 2000000, MAX_EVENTS = 2000;
  const unescape = value => value.replace(/\\([nN,;\\])/g, (_, c) => c.toLowerCase() === 'n' ? ' ' : c);
  function fields(value) {
    const m = /^(\d{4})(\d{2})(\d{2})(?:T(\d{2})(\d{2})(\d{2})?(Z)?)?$/.exec(value);
    if (!m) throw Error('Unsupported calendar date');
    const parts = m.slice(1, 7).map(v => Number(v || 0));
    const [y, mo, d, h, mi, s] = parts;
    if (y < 1900 || y > 2200 || mo < 1 || mo > 12 || d < 1 || d > 31 || h > 23 || mi > 59 || s > 59) throw Error('Invalid calendar date');
    const utc = Date.UTC(y, mo - 1, d, h, mi, s), check = new Date(utc);
    if (check.getUTCFullYear() !== y || check.getUTCMonth() !== mo - 1 || check.getUTCDate() !== d) throw Error('Invalid calendar date');
    return {parts, utc, timed: !!m[4], z: !!m[7]};
  }
  function dateValue(property) {
    const {value, params} = property, f = fields(value);
    if (params.VALUE === 'DATE' || !f.timed) {
      if (f.timed) throw Error('Invalid all-day date');
      return {value: new Date(f.utc).toISOString().slice(0, 10), allDay: true};
    }
    if (f.z) return {value: new Date(f.utc).toISOString(), allDay: false};
    const format = new Intl.DateTimeFormat('en-US', {timeZone: params.TZID || 'America/Los_Angeles', year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',second:'2-digit',hourCycle:'h23'});
    function localTime(utc) {
      const p = Object.fromEntries(format.formatToParts(new Date(utc)).map(x => [x.type, x.value]));
      return Date.UTC(+p.year, +p.month - 1, +p.day, +p.hour, +p.minute, +p.second);
    }
    let guess = f.utc;
    for (let i = 0; i < 4; i++) {const difference = f.utc - localTime(guess); if (!difference) break; guess += difference;}
    if (localTime(guess) !== f.utc) throw Error('Nonexistent local time');
    return {value: new Date(guess).toISOString(), allDay: false};
  }
  function parse(raw) {
    if (typeof raw !== 'string' || new TextEncoder().encode(raw).length > MAX_BYTES) throw Error('Calendar file is too large (2 MB maximum).');
    if (!raw.includes('BEGIN:VCALENDAR') || !raw.includes('END:VCALENDAR')) throw Error('Select a valid .ics calendar file.');
    const lines = raw.replace(/\r?\n[ \t]/g, '').split(/\r?\n/);
    if (lines.length > 40000) throw Error('Calendar file has too many entries.');
    const events = new Map(); let obj = null, skipped = 0, seen = 0;
    for (const line of lines) {
      if (line === 'BEGIN:VEVENT') {obj = Object.create(null); continue;}
      if (line === 'END:VEVENT') {
        if (++seen > MAX_EVENTS) throw Error('Import at most 2,000 calendar entries at a time.');
        try {
          if (!obj || !obj.DTSTART || !obj.SUMMARY || obj.RRULE || obj['RECURRENCE-ID']) throw Error('Unsupported event');
          const start = dateValue(obj.DTSTART), finish = obj.DTEND ? dateValue(obj.DTEND) : null;
          const title = unescape(obj.SUMMARY.value).trim(), location = unescape(obj.LOCATION?.value || '');
          const id = obj.UID?.value || start.value + '|' + title;
          if (!title || title.length > 300 || location.length > 500 || id.length > 500) throw Error('Invalid event fields');
          if (finish && (finish.allDay !== start.allDay || new Date(finish.value) <= new Date(start.value))) throw Error('Invalid end');
          const end = finish?.value || (start.allDay ? new Date(new Date(start.value).getTime() + 86400000).toISOString().slice(0, 10) : null);
          events.set(id, {id, title, location, start:start.value, end, allDay:start.allDay, status:(obj.STATUS?.value || '').toUpperCase().slice(0, 30)});
        } catch {skipped++;}
        obj = null; continue;
      }
      if (obj && line.includes(':')) {
        const colon = line.indexOf(':'), [name, ...parameters] = line.slice(0, colon).split(';');
        const allowed = ['DTSTART','DTEND','SUMMARY','UID','LOCATION','STATUS','RRULE','RECURRENCE-ID'];
        if (!allowed.includes(name.toUpperCase())) continue;
        const params = Object.create(null);
        for (const param of parameters) {const i=param.indexOf('='); if(i>0) params[param.slice(0,i).toUpperCase()]=param.slice(i+1).replace(/^"|"$/g,'');}
        obj[name.toUpperCase()] = {value:line.slice(colon+1),params};
      }
    }
    return {events:[...events.values()],skipped};
  }
  window.BeaconICS = {parse};
})();

/* Shared university dates, separate from sports and personal browser data. */
(() => {
  'use strict';
  let data = {verified:false, events:[], source:'https://bushnell.edu/academics/academic-calendars/'};
  const date = value => /^\d{4}-\d{2}-\d{2}$/.test(value || '') && !Number.isNaN(Date.parse(value)) && new Date(value).toISOString().slice(0, 10) === value;
  function validate(input) {
    if (!input || input.verified !== true || !Array.isArray(input.events)) throw Error('University academic dates are not available yet.');
    const ids = new Set();
    for (const event of input.events) {
      if (!event.id || ids.has(event.id) || !event.title || !date(event.start) || !date(event.end) || event.end <= event.start || !['holiday','break','deadline','term'].includes(event.kind)) throw Error('University academic dates could not be verified.');
      ids.add(event.id);
    }
    return input;
  }
  async function load() {
    try {
      const response = await fetch('academic-calendar.json', {cache:'no-cache'});
      if (!response.ok) throw Error('University academic dates are unavailable.');
      data = validate(await response.json());
      data.error = '';
    } catch (error) {data = {...data, verified:false, events:[], error:error.message};}
    document.dispatchEvent(new Event('beacon:academic'));
    return data;
  }
  const forDay = day => data.verified ? data.events.filter(event => event.start <= day && day < event.end) : [];
  const kind = day => {const events=forDay(day);return events.some(e=>e.kind==='holiday')?'holiday':events.some(e=>e.kind==='break')?'break':'';};
  window.BeaconAcademic = {load, forDay, kind, status:()=>({...data}), find:id=>data.events.find(e=>e.id===id)};
})();

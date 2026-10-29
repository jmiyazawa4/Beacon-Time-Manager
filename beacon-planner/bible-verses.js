/* NIV is supplied by Bible Gateway's public verse-of-the-day widget.
   No NIV verse collection is bundled, persisted, or substituted from another translation. */
(() => {
  'use strict';
  let verse = null, requestedDay = '', inFlight = null;
  let status = {state: 'idle', error: ''};
  const dayKey = () => {const now = new Date(); return `${now.getFullYear()}-${now.getMonth()+1}-${now.getDate()}`;};
  function signal() {document.dispatchEvent(new Event('beacon:verse'));}
  function current() {return requestedDay === dayKey() ? verse : null;}
  function load(force = false) {
    if (inFlight) return inFlight;
    if (!force && requestedDay === dayKey() && verse) return Promise.resolve(verse);
    requestedDay = dayKey(); verse = null; status = {state: 'loading', error: ''}; signal();
    inFlight = fetch('/api/verse', {cache:'no-store'}).then(async response => {
      const data = await response.json();
      if (!response.ok) throw Error(data.error || 'The NIV verse service is unavailable.');
      if (data.translation !== 'NIV' || !data.text || !data.reference || !data.copyright) throw Error('The NIV response is missing the verse or publisher attribution.');
      verse = {...data, date:new Date().toLocaleDateString('en-US', {month:'long',day:'numeric',year:'numeric'})};
      status = {state:'ready', error:''}; return verse;
    }).catch(error => {
      verse = null; status = {state:'error', error:error.message || 'Unable to load the NIV verse. Retry or read it on Bible Gateway.'}; return null;
    }).finally(() => {inFlight = null; signal();});
    return inFlight;
  }
  window.BeaconVerses = {current, load, status: () => ({...status}), dayKey};
})();

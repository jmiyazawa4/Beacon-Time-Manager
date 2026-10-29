/* Planning estimates; official end times and all-day/TBA entries take precedence. */
(() => {
  'use strict';
  const minutes = {baseball:195,softball:105,'mens-basketball':120,'womens-basketball':120,'mens-soccer':120,'womens-soccer':120,'womens-volleyball':120,'beach-volleyball':90,'mens-cross-country':180,'womens-cross-country':180,'mens-track-and-field':360,'womens-track-and-field':360,'mens-golf':300,'womens-golf':300,esports:120};
  const normalize = text => String(text || '').normalize('NFKC').toLowerCase().replace(/^(?:vs\.?|at)\s+/, '').replace(/[^a-z0-9]/g, '');
  function unique(events) {
    const result=[],ids=new Set();
    // Official entries win over matching calendar imports. Distinct official game
    // IDs remain separate, even with identical TBA starts (real doubleheaders).
    const sorted=[...events].sort((a,b)=>Number(b.source==='Official Bushnell schedule')-Number(a.source==='Official Bushnell schedule'));
    for(const e of sorted){
      const identity=e.sport+'|'+e.source+'|'+(e.id||e.key);
      if((e.id||e.key)&&ids.has(identity))continue;
      const same=result.find(x=>x.sport===e.sport&&!!x.allDay===!!e.allDay&&
        (e.allDay?x.start===e.start:Date.parse(x.start)===Date.parse(e.start))&&normalize(x.title)===normalize(e.title)&&
        (!x.location||!e.location||normalize(x.location)===normalize(e.location))&&
        !(x.source==='Official Bushnell schedule'&&e.source==='Official Bushnell schedule'));
      if(same)continue;
      ids.add(identity);result.push(e);
    }
    return result;
  }
  function timing(event) {
    const start=new Date(event.start),published=event.end?new Date(event.end):null;
    const known=!!published&&Number.isFinite(+published)&&published>start;
    const duration=minutes[event.sport]||120;
    return {finish:known?published:new Date(+start+duration*60000),estimated:!known&&!event.allDay,minutes:duration};
  }
  // Assign a stable column for the whole block, including overlaps starting later.
  function layout(events){
    const sorted=[...events].sort((a,b)=>a.start-b.start||a.end-b.end);let group=[],end=-1;
    const flush=()=>{const lanes=[];for(const e of group){let lane=lanes.findIndex(t=>t<=e.start);if(lane<0)lane=lanes.length;lanes[lane]=e.end;e.lane=lane;}for(const e of group)e.lanes=lanes.length;group=[];};
    for(const e of sorted){if(group.length&&e.start>=end){flush();end=-1;}group.push(e);end=Math.max(end,e.end);}flush();return sorted;
  }
  window.BeaconSports={unique,timing,layout,minutes:Object.freeze(minutes)};
})();

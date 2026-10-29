/* Local CSV adapter: ambiguous times stay date-only and are explicitly flagged. */
(() => {
 'use strict';
 const clean=s=>String(s||'').trim(),header=s=>clean(s).toLowerCase().replace(/[^a-z0-9]/g,'');
 function rows(text){
  if(text.length>2000000)throw Error('CSV is too large (2 MB maximum).');
  const out=[];let row=[],field='',quoted=false;
  for(let i=0;i<text.length;i++){
   const c=text[i];
   if(c==='"'){if(quoted&&text[i+1]==='"'){field+='"';i++;}else if(quoted||!field)quoted=!quoted;else throw Error('Invalid CSV quoting.');}
   else if(c===','&&!quoted){row.push(field);field='';}
   else if((c==='\n'||c==='\r')&&!quoted){if(c==='\r'&&text[i+1]==='\n')i++;row.push(field);if(row.some(x=>clean(x)))out.push(row);row=[];field='';if(out.length>2001)throw Error('CSV has too many entries (2,000 maximum).');}
   else field+=c;
  }
  if(quoted)throw Error('CSV has an unfinished quoted field.');row.push(field);if(row.some(x=>clean(x)))out.push(row);
  if(out.length>2001)throw Error('CSV has too many entries (2,000 maximum).');return out;
 }
 function date(value,year){
  value=clean(value);const weekday=/\((Sunday|Monday|Tuesday|Wednesday|Thursday|Friday|Saturday)\)/i.exec(value)?.[1];value=value.replace(/\([^)]*\)/g,'').trim();
  let y,m,d,match;
  if((match=/^(\d{4})-(\d{1,2})-(\d{1,2})$/.exec(value))){[,y,m,d]=match;}
  else if((match=/^(\d{1,2})\/(\d{1,2})(?:\/(\d{4}))?$/.exec(value))){m=match[1];d=match[2];y=match[3]||year;}
  else if((match=/^([A-Za-z]+)\s+(\d{1,2})(?:,?\s+(\d{4}))?$/.exec(value))){m=['jan','feb','mar','apr','may','jun','jul','aug','sep','oct','nov','dec'].indexOf(match[1].slice(0,3).toLowerCase())+1;d=match[2];y=match[3]||year;}
  else throw Error('Unrecognized date');
  y=+y;m=+m;d=+d;const check=new Date(Date.UTC(y,m-1,d));
  if(y<1900||y>2200||m<1||m>12||d<1||check.getUTCMonth()!==m-1||check.getUTCDate()!==d)throw Error('Invalid date');
  if(weekday&&['sunday','monday','tuesday','wednesday','thursday','friday','saturday'][check.getUTCDay()]!==weekday.toLowerCase())throw Error('Weekday does not match selected year');
  return `${y}-${String(m).padStart(2,'0')}-${String(d).padStart(2,'0')}`;
 }
 function clock(text,suffix,allow24=false){const m=/^(\d{1,2})(?::(\d{2}))?\s*(am|pm)?$/i.exec(clean(text));if(!m)return null;let h=+m[1],mi=+(m[2]||0),meridiem=(m[3]||suffix||'').toLowerCase();if(mi>59||h>23)return null;if(meridiem){if(h<1||h>12)return null;h=h%12+(meridiem==='pm'?12:0);}else if(h<=12&&!allow24)return null;return h*60+mi;}
 const stamp=(day,minutes)=>day.replaceAll('-','')+'T'+String(Math.floor(minutes/60)).padStart(2,'0')+String(minutes%60).padStart(2,'0')+'00';
 const escape=s=>String(s).replace(/\\/g,'\\\\').replace(/\r?\n/g,'\\n').replace(/,/g,'\\,').replace(/;/g,'\\;');
 function hash(s){let n=2166136261;for(const c of s)n=Math.imul(n^c.charCodeAt(0),16777619);return (n>>>0).toString(16);}
 function parse(text,{year=new Date().getFullYear()}={}){
  const table=rows(text.replace(/^\uFEFF/,''));if(table.length<2)throw Error('CSV needs a header and at least one entry.');
  const keys=table.shift().map(header),index=(...names)=>keys.findIndex(k=>names.includes(k));
  const di=index('date'),ti=index('event','title','activity','name'),range=index('duration','time'),si=index('starttime','start'),ei=index('endtime','end');
  if(di<0||ti<0)throw Error('CSV must include Date and Event (or Title) columns.');
  const li=index('location'),ai=index('requiredattendance','attendance','group'),ni=index('description','notes');
  const events=[],warnings=[];let skipped=0,needsReview=0;const seen=new Set();
  table.forEach((row,i)=>{try{
   const get=column=>column<0?'':clean(row[column]);const title=get(ti).slice(0,300);if(!title)throw Error('Missing event title');
   const day=date(get(di),year),raw=get(range),time=raw.replace(/\([^)]*\)/g,'').trim();let start=null,end=null;
   if(si>=0){start=clock(get(si),null,true);end=clock(get(ei),null,true);}
   else {const parts=time.split(/\s*[-–—]\s*/);if(parts.length===2){const endSuffix=/(am|pm)\s*$/i.exec(parts[1])?.[1];start=clock(parts[0],endSuffix);end=clock(parts[1]);}}
   const timed=start!==null&&end!==null&&end>start,explicitAllDay=/^all\s*day$/i.test(time)||/^off$/i.test(title);
   const attendance=get(ai).slice(0,300),description=get(ni).slice(0,1000),location=get(li).slice(0,500);
   const uid='csv-'+hash([day,title,attendance,timed?start:time].join('|'));if(seen.has(uid))return;seen.add(uid);
   const item={id:uid,title,location,attendance,description,category:/practice|early work|weights|lift/i.test(title)?'Practice':'Other',allDay:!timed,timeUnknown:!timed&&!explicitAllDay,timeLabel:explicitAllDay?'All day':timed?'':(raw||[get(si),get(ei)].filter(Boolean).join('–')||'Time not supplied')+' · confirm time/end',status:''};
   if(timed){
    const ics='BEGIN:VCALENDAR\nBEGIN:VEVENT\nUID:'+uid+'\nSUMMARY:'+escape(title)+'\nDTSTART;TZID=America/Los_Angeles:'+stamp(day,start)+'\nDTEND;TZID=America/Los_Angeles:'+stamp(day,end)+'\nEND:VEVENT\nEND:VCALENDAR';
    const parsed=window.BeaconICS.parse(ics).events[0];if(!parsed)throw Error('Invalid local time');item.start=parsed.start;item.end=parsed.end;item.timeLabel=time;
   }else{item.start=day;item.end=null;if(!explicitAllDay)needsReview++;}
   events.push(item);
  }catch(error){skipped++;if(warnings.length<8)warnings.push('Row '+(i+2)+': '+error.message);}});
  if(!events.length)throw Error(warnings[0]||'No supported events found.');return {events,skipped,needsReview,warnings};
 }
 window.BeaconCSV={parse};
})();

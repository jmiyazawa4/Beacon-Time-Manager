/* Bundled KJV verses and a licensed yearly passage-reference plan. No Bible API. */
(() => {
  'use strict';
  let content=null,inFlight=null,verse=null,selectedDay='',state={state:'idle',error:''};
  const dayKey=()=>{const now=new Date();return `${now.getFullYear()}-${now.getMonth()+1}-${now.getDate()}`;};
  const signal=()=>document.dispatchEvent(new Event('beacon:verse'));
  function forDate(now){
    if(!content)return null;
    const leap=now.getMonth()===1&&now.getDate()===29;
    const index=Math.round((Date.UTC(2001,now.getMonth(),now.getDate())-Date.UTC(2001,0,1))/86400000);
    const reading=leap?[]:content.plan.days[index],entry=leap?content.verses.leapDay:content.verses.days[index];
    return {...entry,translation:'KJV',copyright:content.verses.copyright,passages:reading,planName:content.plan.name,planSource:content.plan.source,catchUp:leap,link:'https://www.biblegateway.com/passage/?search='+encodeURIComponent(entry.reference)+'&version=KJV',date:now.toLocaleDateString('en-US',{month:'long',day:'numeric',year:'numeric'})};
  }
  function selectToday(){verse=forDate(new Date());selectedDay=dayKey();state={state:'ready',error:''};signal();return verse;}
  function current(){return selectedDay===dayKey()?verse:null;}
  function load(){
    if(content)return Promise.resolve(selectToday());
    if(inFlight)return inFlight;
    state={state:'loading',error:''};signal();
    inFlight=Promise.all(['reading-plan.json','daily-verses.json'].map(async file=>{const response=await fetch(file);if(!response.ok)throw Error('Saved Bible reading content is unavailable.');return response.json();})).then(([plan,verses])=>{
      if(plan.days?.length!==365||verses.days?.length!==365||verses.translation!=='KJV')throw Error('Saved Bible reading content could not be verified.');
      content={plan,verses};return selectToday();
    }).catch(error=>{state={state:'error',error:error.message};verse=null;signal();return null;}).finally(()=>{inFlight=null;});
    return inFlight;
  }
  window.BeaconVerses={current,load,status:()=>({...state}),dayKey,forDate};
})();

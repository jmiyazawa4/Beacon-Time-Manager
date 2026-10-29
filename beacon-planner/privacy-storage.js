/* Personal planner data is local-only; private-session mode never persists it. */
(() => {
  'use strict';
  const DATA='beacon-planner-v1', MODE='beacon-private-session';
  const lockedPreview=window.BEACON_REVIEW_PRIVATE===true;
  let privateMode=lockedPreview, unavailable=false, erasureFailed=false;
  try {privateMode=lockedPreview||localStorage.getItem(MODE)==='1'; if(privateMode)localStorage.removeItem(DATA);} catch {privateMode=true;unavailable=true;erasureFailed=true;}
  function changed(){document.dispatchEvent(new Event('beacon:privacy'));}
  function load(){if(privateMode)return null;try{return JSON.parse(localStorage.getItem(DATA));}catch{return null;}}
  function save(data){if(privateMode)return;try{localStorage.setItem(DATA,JSON.stringify(data));erasureFailed=false;}catch{privateMode=true;unavailable=true;erasureFailed=true;changed();}}
  function setPrivate(enabled){
    if(lockedPreview&&!enabled){privateMode=true;changed();return true;}
    if(enabled){
      // Remove durable planner data before indicating that private mode is on.
      try{localStorage.removeItem(DATA);localStorage.setItem(MODE,'1');erasureFailed=false;}catch{unavailable=true;erasureFailed=true;}
      privateMode=true;
    }else{
      try{localStorage.removeItem(MODE);privateMode=false;unavailable=false;}catch{privateMode=true;unavailable=true;erasureFailed=true;}
    }
    changed();return privateMode;
  }
  window.addEventListener('storage',event=>{if(event.key===MODE&&event.newValue==='1'){privateMode=true;try{localStorage.removeItem(DATA);}catch{erasureFailed=true;}changed();}});
  window.BeaconPrivacy={load,save,setPrivate,status:()=>({privateMode,unavailable,erasureFailed,lockedPreview})};
})();

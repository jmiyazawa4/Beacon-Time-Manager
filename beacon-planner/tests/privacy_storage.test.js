const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const source=fs.readFileSync(path.join(__dirname,'../privacy-storage.js'),'utf8');
function setup(locked=false){
 const data=new Map([['beacon-planner-v1','{"student":"synthetic-test"}']]);let failRemove=false,failSet=false;
 const context={window:{BEACON_REVIEW_PRIVATE:locked,addEventListener(){}},document:{dispatchEvent(){}},Event:class {},localStorage:{getItem:key=>data.get(key)||null,setItem:(key,value)=>{if(failSet)throw Error('blocked');data.set(key,value)},removeItem:key=>{if(failRemove)throw Error('blocked');data.delete(key)}},JSON};
 vm.runInNewContext(source,context);
 return {api:context.window.BeaconPrivacy,data,removeFailure:value=>failRemove=value,setFailure:value=>failSet=value};
}
let s=setup();s.api.save({student:'synthetic-new'});assert.equal(JSON.parse(s.data.get('beacon-planner-v1')).student,'synthetic-new');s.api.setPrivate(true);assert.equal(s.data.has('beacon-planner-v1'),false);s.api.save({student:'not-saved'});assert.equal(s.data.has('beacon-planner-v1'),false);
s=setup(true);assert.equal(s.data.has('beacon-planner-v1'),false);assert.equal(s.api.setPrivate(false),true);assert.equal(s.api.status().lockedPreview,true);
s=setup();s.removeFailure(true);s.api.setPrivate(true);assert.equal(s.api.status().privateMode,true);assert.equal(s.api.status().erasureFailed,true);assert.equal(s.api.load(),null);assert.equal(s.data.has('beacon-planner-v1'),true);
s=setup();s.setFailure(true);s.api.save({student:'not-saved'});assert.equal(s.api.status().privateMode,true);assert.equal(s.api.status().erasureFailed,true);s.setFailure(false);s.api.setPrivate(false);s.api.save({student:'saved-again'});assert.equal(s.api.status().erasureFailed,false);
console.log('PASS: private mode never saves; preview mode cannot be disabled; storage failures report that older data may remain');

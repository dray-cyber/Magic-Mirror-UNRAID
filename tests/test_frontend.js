// Unit tests of real polling/render functions with a minimal DOM adapter.
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const elements=new Map();const element=key=>{if(!elements.has(key))elements.set(key,{hidden:true,textContent:''});return elements.get(key);};
const sandbox={structuredClone,console:{error(){}},URL,URLSearchParams,Date,Intl,setTimeout:()=>0,clearTimeout(){},location:{hash:'',pathname:'/'},sessionStorage:{getItem:()=>'',setItem(){}},history:{replaceState(){}},document:{querySelector:s=>s==='dialog[open]'?null:element(s),querySelectorAll:()=>[]}};
vm.createContext(sandbox);
const source=fs.readFileSync(require('node:path').join(__dirname,'../app/static/app.js'),'utf8');
vm.runInContext(source.slice(0,source.indexOf("$('#themeSelect').innerHTML=")),sandbox);
(async()=>{
 await vm.runInContext(`(async()=>{api=async()=>({config:{}});render=()=>{throw new Error('broken widget')};await poll();})()`,sandbox);
 assert.match(element('#toast').textContent,/Display error: broken widget/);
 assert.doesNotMatch(element('#toast').textContent,/disconnected/);
 await vm.runInContext(`(async()=>{api=async()=>{const e=new Error('Unauthorized');e.status=401;throw e;};await poll();})()`,sandbox);
 assert.match(element('#pairError').textContent,/Session expired/);assert.equal(element('#pair').hidden,false);
 const html=vm.runInContext(`renderers.weather=()=>{throw new Error('missing data')};renderPanel('weather')`,sandbox);
 assert.match(html,/This panel could not display/);
 await vm.runInContext(`(async()=>{api=async()=>({config:{}});render=()=>{};await poll();})()`,sandbox);
 assert.equal(vm.runInContext('lastPollError',sandbox),'');
 for(const z of [.45,.5,.67,.8,1,1.1,1.25]){sandbox.w=1920/z;sandbox.h=1080/z;const g=vm.runInContext('tvGeometry(w,h)',sandbox);assert.ok(Math.abs(g.width-1920)<.001);assert.ok(Math.abs(g.height-1080)<.001);assert.ok(Math.abs(g.scale*z-1)<.001);}
 sandbox.keys=['clock','agenda','assignments','commute','weather','notes'];
 assert.equal(vm.runInContext("JSON.stringify(themeLayout(keys,'lcars',860))===JSON.stringify(themeLayout(keys,'red-alert',860))",sandbox),true);
 assert.equal(vm.runInContext("JSON.stringify(themeLayout(keys,'lcars',860))!==JSON.stringify(themeLayout(keys,'ocean',860))",sandbox),true);
 assert.equal(vm.runInContext("snapTile({x:0,y:0,w:30,h:200},false,12.3,25).x",sandbox),12);
 assert.equal(vm.runInContext("snapTile({x:0,y:0,w:30,h:200},false,12.3,25).y",sandbox),24);
 assert.equal(vm.runInContext("snapTile({x:0,y:0,w:30,h:200},true,2.2,30).h",sandbox),228);
 const inventory=vm.runInContext('Object.keys(tileInventory({clock:{x:0,y:0,w:30,h:200}}))',sandbox);
 for(const key of ['radar','classes','sensors','workshop','connections','yearprogress','mission','schoolcommute'])assert.ok(inventory.includes(key));
 const full=vm.runInContext("tileInventory({clock:{x:0,y:1440,w:32,h:280}})",sandbox);
 for(const item of Object.values(full)){assert.ok(item.y<=3000);assert.ok(item.x+item.w<=100.1);assert.ok(item.h>=100&&item.h<=1600);}
 sandbox.saved={clock:{x:0,y:0,w:32,h:280},radar:{x:0,y:1100,w:32,h:280}};
 const fitted=vm.runInContext("fitVisibleLayout(saved,['clock','radar'],'lcars',700)",sandbox);for(const item of Object.values(fitted))assert.ok(item.y+item.h<=700.01);
 sandbox.weatherFixture={timezone:'America/Chicago',daily:{sunrise:['2026-11-17T06:00','2026-11-18T06:00'],sunset:['2026-11-17T17:00','2026-11-18T17:00']}};
 assert.equal(vm.runInContext("solarRemaining(weatherFixture,Date.parse('2026-11-17T16:00:00Z')).hours",sandbox),7);
 assert.equal(vm.runInContext("solarRemaining(weatherFixture,Date.parse('2026-11-18T02:00:00Z')).hours",sandbox),10);
 assert.equal(vm.runInContext("solarRemaining(weatherFixture,Date.parse('2026-11-18T02:00:00Z')).label",sandbox),'Moonlight Remaining');
 sandbox.checkbox={dataset:{task:'assignment-123'},checked:true,disabled:false};
 await vm.runInContext(`(async()=>{const oldQuery=document.querySelectorAll;document.querySelectorAll=s=>s==='[data-task]'?[checkbox]:[];let sent;action=async body=>{sent=body;};bindPanelEvents();await checkbox.onchange();if(sent.key!=='assignment-123'||sent.done!==true)throw Error('Completion not submitted');action=async()=>{throw Error('Save failed')};checkbox.checked=true;await checkbox.onchange();if(checkbox.checked||checkbox.disabled)throw Error('Checkbox failed rollback');document.querySelectorAll=oldQuery;})()`,sandbox);
 assert.equal(vm.runInContext('weekendAlertDue(NaN,1000)',sandbox),true);
 assert.equal(vm.runInContext('weekendAlertDue(1000,480999)',sandbox),false);
 assert.equal(vm.runInContext('weekendAlertDue(1000,481000)',sandbox),true);
 assert.equal(vm.runInContext('WEEKEND_VISIBLE',sandbox),12000);
 console.log('Five-pulse timeout and eight-minute repeat checks passed');
 console.log('Assignment completion submission and failure rollback passed');
 console.log('Day/night hours and ZIP timezone checks passed');
 assert.equal(fitted.radar.x,sandbox.saved.radar.x);assert.equal(fitted.radar.w,sandbox.saved.radar.w);
 assert.ok(Math.abs(fitted.radar.y/fitted.radar.h-sandbox.saved.radar.y/sandbox.saved.radar.h)<.001);
 console.log('Saved row fitting preserves relative positions');
 console.log('Off-screen saved tiles refit into available height');
 console.log('Optional tile inventory stays inside server bounds');
 console.log('Restored tile inventory checks passed');
 console.log('Grid snap movement and resize checks passed');
 console.log('Theme layout identity and variation checks passed');
 console.log('Zoom geometry at 45%, 50%, 67%, 80%, 100%, 110%, 125% passed');
 console.log('4 frontend polling/render regression checks passed');
})().catch(e=>{console.error(e);process.exitCode=1});


require('./test_fan_display.js');

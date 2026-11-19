const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict'),path=require('node:path');
const text=fs.readFileSync(path.join(__dirname,'../app/static/app.js'),'utf8');
const animations=[];
function node(){return {style:{},childNodes:[],get firstChild(){return this.childNodes[0]},append(...children){for(const c of children){if(c.parent){c.parent.childNodes=c.parent.childNodes.filter(x=>x!==c);}c.parent=this;this.childNodes.push(c);}},replaceChildren(...children){this.childNodes=[];this.append(...children)},setAttribute(){},querySelectorAll(){return []},cloneNode(){return node()},getBoundingClientRect(){return {height:500}},animate(){const animation={currentTime:0,cancel(){this.cancelled=true;}};animations.push(animation);return animation;}};}
const body=node();Object.assign(body,{clientWidth:300,clientHeight:100,closest:()=>({dataset:{key:'agenda'}}),getAnimations:()=>animations.filter(a=>!a.cancelled)});body.append(node());
const context={arranging:false,state:{config:{tv_mode:false}},$$:()=>[body],document:{createElement:node},getComputedStyle:()=>({paddingTop:'0',paddingBottom:'0'}),tvGeometry:()=>({scale:1})};vm.createContext(context);
vm.runInContext(text.slice(text.indexOf('function saveLoopPosition('),text.indexOf('function renderPanel(')),context);
vm.runInContext('setupLoops()',context);const first=body._loopAnimation;assert.ok(first);assert.equal(first.currentTime,0);assert.equal(body.onmouseenter,null);
first.currentTime=5300;vm.runInContext('setupLoops()',context);assert.equal(body._loopAnimation,first);assert.equal(first.currentTime,5300);assert.ok(!first.cancelled);
body.clientHeight=120;vm.runInContext('setupLoops()',context);assert.ok(first.cancelled);assert.notEqual(body._loopAnimation,first);assert.equal(body._loopAnimation.currentTime,5300);
console.log('Autoscroll preserves animation across polls and position across resize; no hover pause');

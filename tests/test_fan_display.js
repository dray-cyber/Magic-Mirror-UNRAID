const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const text=fs.readFileSync(require('node:path').join(__dirname,'../app/static/app.js'),'utf8');const context={};vm.createContext(context);vm.runInContext(text.slice(text.indexOf('function fanPercentLabel('),text.indexOf('function renderIdracFooter(')),context);
assert.equal(context.fanPercentLabel({fan_percent:19,control:{mode:'manual'}}),'19%');
assert.equal(context.fanPercentLabel({control:{mode:'manual',percent:25}}),'25%');
assert.equal(context.fanPercentLabel({control:{mode:'automatic'}}),'—% (Auto)');
assert.equal(context.fanPercentLabel({control:{mode:'error'}}),'—% (control error)');
console.log('Fan percentage display and automatic/error-mode checks passed');

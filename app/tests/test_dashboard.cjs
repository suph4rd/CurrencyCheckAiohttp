const vm = require('node:vm');
const fs = require('node:fs');
const path = require('node:path');
const scriptPath = name => path.join(__dirname, '..', 'static', 'js', name);
const assert = require('node:assert/strict');
class Element {
    constructor() { this.dataset = {}; this.listeners = {}; this.hidden = false; this.value = ''; this.children = []; this.textContent = ''; this.classList = {toggle() {}, remove() {}}; }
    addEventListener(event, fn) { this.listeners[event] = fn; }
    setAttribute(key, value) { this[key] = value; }
    append(...children) { this.children.push(...children); }
    querySelectorAll() { return this.rows || []; }
    querySelector() { return (this.rows || [])[0]; }
    set innerHTML(value) { this.rows = value.split(',').filter(Boolean).map(name => {const el = new Element(); el.dataset.bankName = name; return el;}); }
}
const messages = {loading:'loading', refreshing:'refreshing', load_error:'load error', refresh_error:'refresh error', retry:'retry', count:'{visible} of {total} records', empty:'empty'};
const sections = [0,1].map(i => { const el = new Element(); el.dataset.url = `/source${i}`; el.parts = Object.fromEntries(['search','refresh','status','content','count','no-results'].map(k => [`[data-${k}]`, new Element()])); el.querySelector = selector => el.parts[selector]; return el; });
let requests = [];
const document = {documentElement:{lang:'en'}, getElementById:()=>({textContent:JSON.stringify(messages)}), querySelectorAll:()=>sections, createElement:()=>new Element()};
const context = {document, AbortController, window:{setTimeout, clearTimeout}, fetch:(url)=>new Promise((resolve,reject)=>requests.push({url,resolve,reject}))};
vm.runInNewContext(fs.readFileSync(scriptPath('dashboard.js'), 'utf8'),context);
const tick = () => new Promise(resolve=>setImmediate(resolve));
(async () => {
    assert.equal(requests.length,2);
    sections[0].parts['[data-refresh]'].listeners.click();
    assert.equal(requests.length,2,'concurrent duplicate must be blocked');
    requests[0].resolve({ok:true,text:async()=> 'Alpha Bank,Beta Bank'});
    requests[1].reject(new Error('upstream failed'));
    await tick();
    const first=sections[0].parts;
    assert.equal(first['[data-count]'].textContent,'2 of 2 records');
    assert.equal(sections[1].dataset.state,'error');
    first['[data-search]'].value='BETA'; first['[data-search]'].listeners.input();
    assert.equal(first['[data-count]'].textContent,'1 of 2 records');
    first['[data-refresh]'].listeners.click(); requests[2].reject(new Error('failed')); await tick();
    assert.equal(first['[data-content]'].rows.length,2,'failed refresh retains rows');
    assert.equal(first['[data-status]'].textContent,'refresh error');
    first['[data-status]'].children.at(-1).listeners.click();
    requests[3].resolve({ok:true,text:async()=> 'Beta Bank,Gamma Bank'}); await tick();
    assert.equal(first['[data-search]'].value,'BETA');
    assert.equal(first['[data-count]'].textContent,'1 of 2 records');
    first['[data-search]'].value='missing'; first['[data-search]'].listeners.input();
    assert.equal(first['[data-no-results]'].hidden,false);
    const select = new Element();
    let ready, change;
    const media={matches:true,addEventListener:(_,fn)=>change=fn};
    const root={dataset:{}};
    vm.runInNewContext(fs.readFileSync(scriptPath('theme.js'), 'utf8'),{document:{documentElement:root,addEventListener:(_,fn)=>ready=fn,querySelectorAll:()=>[select]},window:{matchMedia:()=>media,localStorage:{getItem(){throw new Error('blocked')},setItem(){throw new Error('blocked')}}}});
    assert.equal(root.dataset.theme,'dark'); ready();
    media.matches=false; change(); assert.equal(root.dataset.theme,'light');
    select.value='dark';select.listeners.change();assert.equal(root.dataset.theme,'dark');
    change();assert.equal(root.dataset.theme,'dark');
    select.value='system';select.listeners.change();assert.equal(root.dataset.theme,'light');
    const savedRoot = {dataset: {}};
    let savedReady;
    let storedValue = 'light';
    const savedSelect = new Element();
    vm.runInNewContext(fs.readFileSync(scriptPath('theme.js'), 'utf8'), {
        document: {
            documentElement: savedRoot,
            addEventListener: (_, fn) => savedReady = fn,
            querySelectorAll: () => [savedSelect],
        },
        window: {
            matchMedia: () => media,
            localStorage: {
                getItem: () => storedValue,
                setItem: (_, value) => storedValue = value,
            },
        },
    });
    assert.equal(savedRoot.dataset.theme, 'light');
    savedReady();
    assert.equal(savedSelect.value, 'light');
    savedSelect.value = 'dark';
    savedSelect.listeners.change();
    assert.equal(storedValue, 'dark', 'manual selection must persist');
    console.log('Client checks passed: independent loading, duplicate prevention, filtering, stale data, retry, preserved search, empty search, system/manual theme, blocked storage.');
})().catch(error => {
    console.error(error);
    process.exitCode = 1;
});

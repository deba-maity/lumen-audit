// Optional browser QA. Run with an existing Electron binary, not with Node.
// Uses a hidden window, project-local browser data, and the demo-only server.
const {app, BrowserWindow, session} = require('electron');
const fs = require('node:fs');
const path = require('node:path');
const {pathToFileURL} = require('node:url');
const assert = require('node:assert/strict');
const root = path.resolve(__dirname, '..');
const artifacts = path.join(root, '.qa', 'browser');
fs.mkdirSync(artifacts, {recursive: true});
app.setPath('userData', path.join(artifacts, 'profile'));
app.setPath('sessionData', path.join(artifacts, 'session'));
app.disableHardwareAcceleration();
app.commandLine.appendSwitch('disable-background-networking');
app.commandLine.appendSwitch('disable-component-update');
app.commandLine.appendSwitch('disable-renderer-backgrounding');
const baseUrl = process.env.LUMEN_TEST_URL;
if (!baseUrl || !baseUrl.startsWith('http://127.0.0.1:')) throw new Error('Set LUMEN_TEST_URL to a running demo-only Lumen server.');
let win;
const errors = [];
const results = [];
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
const js = code => win.webContents.executeJavaScript(code, true);
async function waitFor(expression) {
  for (let i = 0; i < 80; i++) {
    if (await js(expression)) return;
    await sleep(75);
  }
  throw new Error('Timed out: ' + expression);
}
async function click(selector) {
  assert(await js(`Boolean(document.querySelector(${JSON.stringify(selector)}))`), 'Missing ' + selector);
  await js(`document.querySelector(${JSON.stringify(selector)}).click()`);
  await sleep(80);
}
function record(name) { results.push(name); process.stdout.write('PASS ' + name + '\n'); }

app.whenReady().then(async () => {
  try {
    session.defaultSession.webRequest.onBeforeRequest((details, callback) => {
      const allowed = details.url.startsWith(baseUrl + '/') || details.url.startsWith('blob:') || details.url.startsWith('data:') || details.url === baseUrl;
      if (!allowed) errors.push('Unexpected network request: ' + details.url);
      callback({cancel: !allowed});
    });
    win = new BrowserWindow({show: false, width: 1480, height: 1100, webPreferences: {contextIsolation: true, nodeIntegration: false, sandbox: true, backgroundThrottling: false, offscreen: true}});
    win.webContents.on('console-message', (_event, details) => {
      if (details.level === 'error') errors.push(details.message);
    });
    win.webContents.on('render-process-gone', (_event, details) => errors.push('Renderer gone: ' + details.reason));
    await win.loadURL(baseUrl);
    await waitFor('Boolean(document.querySelector(".hero-card"))');
    await sleep(300);
    assert.equal(await js('state.config.demo_only'), true);
    assert.equal(await js('state.report.demo'), true);
    record('Demo boots with no live scan');
    await js("localStorage.setItem('lumen-decisions-v2-demo-current','null')");
    await win.reload();
    await waitFor('Boolean(document.querySelector(".hero-card"))');
    await click('[data-page="review"]');
    assert(await js('document.querySelectorAll(".review-card").length > 0'));
    await click('[data-page="overview"]');
    record('Malformed browser review state recovers');
    fs.writeFileSync(path.join(artifacts, 'overview-desktop.png'), (await win.webContents.capturePage()).toPNG());
    await js('window.scrollTo(0,650)');
    await sleep(100);
    fs.writeFileSync(path.join(artifacts, 'storage-map-desktop.png'), (await win.webContents.capturePage()).toPNG());
    await js('window.scrollTo(0,0)');

    await click('[data-action="scan"]');
    assert.match(await js('document.querySelector("dialog").textContent'), /demo-only/);
    assert.equal(await js('Boolean(document.querySelector("#scan-form"))'), false);
    await click('[data-action="close-dialog"]');
    record('Demo blocks live-scan form');
    await click('[data-action="privacy"]');
    win.webContents.sendInputEvent({type:'keyDown',keyCode:'Escape'});
    win.webContents.sendInputEvent({type:'keyUp',keyCode:'Escape'});
    await waitFor('!document.querySelector("dialog")');
    record('Escape closes and removes modal');

    await click('.finding-row');
    assert(await js('Boolean(document.querySelector(".evidence-list"))'));
    await click('[data-action="keep"]');
    record('Evidence drawer and keep decision');

    await js("window.originalStorageSetItem=Storage.prototype.setItem;Storage.prototype.setItem=function(){throw new DOMException('Quota exceeded','QuotaExceededError');};void 0");
    try {
      await click('.finding-row');
      await click('[data-action="keep"]');
      assert.match(await js('document.querySelector("#toast").textContent'), /storage is unavailable/);
    } finally { await js('Storage.prototype.setItem=window.originalStorageSetItem;delete window.originalStorageSetItem'); }
    record('Unavailable review storage gives a persistent warning');

    await click('[data-page="explorer"]');
    fs.writeFileSync(path.join(artifacts,'explorer-desktop.png'),(await win.webContents.capturePage()).toPNG());
    await click('[data-action="folder"]');
    assert(await js('Boolean(state.folder)'));
    assert(await js('document.querySelectorAll(".file-table tbody tr").length < state.report.files.length'));
    await click('[data-action="clear-folder"]');
    record('Folder drill-down and clear filter');
    await js('document.querySelector("#file-search").value = "Brand-assets"; document.querySelector("#file-search").dispatchEvent(new Event("input", {bubbles:true}))');
    assert.equal(await js('document.querySelectorAll(".file-table tbody tr").length'), 3);
    await click('.file-link');
    assert.match(await js('document.querySelector("dialog").textContent'), /Last opened by a person\s*Unknown/);
    await click('[data-action="close-dialog"]');
    record('Inventory search and honest timestamps');
    await click('.file-link');
    await click('[data-action="explain-file"]');
    await waitFor('!state.asking && state.messages.length===2');
    assert(await js('state.messages[1].file_references.length===1'));
    await click('.reference-chips [data-action="file"]');
    assert.match(await js('document.querySelector("dialog").textContent'),/What it likely does/);
    await click('[data-action="close-dialog"]');
    await click('[data-page="explorer"]');
    record('Direct file explanation with navigable file evidence');

    await js('document.querySelector("#file-search").value = "nothing-will-match-this"; document.querySelector("#file-search").dispatchEvent(new Event("input", {bubbles:true}))');
    assert.match(await js('document.querySelector("#file-results").textContent'), /No files/);
    await click('[data-action="reset-filters"]');
    assert.equal(await js('document.querySelectorAll(".file-table tbody tr").length'), 40);
    await click('[data-action="next-files"]');
    assert.equal(await js('state.pageNumber'), 2);
    record('Empty states, filters, and pagination');

    await click('[data-page="review"]');
    await click('[data-kind="duplicates"]');
    assert.equal(await js('document.querySelectorAll(".review-card").length'), 3);
    await click('[data-page="duplicates"]');
    assert.equal(await js('document.querySelectorAll(".duplicate-group").length'), 3);
    record('Review filters and duplicate groups');

    await click('[data-page="history"]');
    await click('[data-action="compare"]');
    await waitFor('Boolean(document.querySelector(".change-stats"))');
    assert.equal(await js('state.comparison.added'), 2);
    assert.equal(await js('state.comparison.removed'), 1);
    fs.writeFileSync(path.join(artifacts, 'changes-desktop.png'), (await win.webContents.capturePage()).toPNG());
    record('Snapshot comparison');

    await click('[data-page="assistant"]');
    await click('[data-action="clear-chat"]');
    await click('[data-question="Explain my duplicate files."]');
    await waitFor('!state.asking && state.messages.length === 2');
    assert.equal(await js('state.messages[1].source'), 'evidence');
    assert(await js('document.querySelectorAll(".reference-chips button").length > 0'));
    await click('.reference-chips button');
    assert(await js('Boolean(document.querySelector(".detail-drawer"))'));
    await click('[data-action="close-dialog"]');
    record('Evidence assistant and citations');

    await js("window.originalApiForFailure=api;api=async(path,...args)=>{if(path==='/api/models')throw new Error('Simulated network failure');return window.originalApiForFailure(path,...args);};void 0");
    const refreshLabel=await js('document.querySelector("[data-action=models]").textContent');
    try {
      await click('[data-action="models"]');
      assert.equal(await js('document.querySelector("[data-action=models]").disabled'),false);
      assert.equal(await js('document.querySelector("[data-action=models]").textContent'),refreshLabel);
    } finally { await js('api=window.originalApiForFailure;delete window.originalApiForFailure'); }
    record('Failed model refresh restores its retry button');

    await js("document.querySelector('#question').value='What does package.json do?';document.querySelector('#question').dispatchEvent(new Event('input',{bubbles:true}));document.querySelector('#model-select').dispatchEvent(new Event('change',{bubbles:true}));");
    assert.equal(await js('document.querySelector("#question").value'),'What does package.json do?');
    await click('[data-page="overview"]');
    await click('[data-page="assistant"]');
    assert.equal(await js('document.querySelector("#question").value'),'What does package.json do?');
    record('Question draft survives engine selection and navigation');

    await click('[data-page="explorer"]');
    await click('.file-link');
    await js("window.originalClipboardWrite=navigator.clipboard.writeText;navigator.clipboard.writeText=async()=>{throw new DOMException('Denied','NotAllowedError');};void 0");
    try {
      const expectedPath=await js('document.querySelector("[data-action=copy-path]").dataset.path');
      await click('[data-action="copy-path"]');
      assert.equal(await js('document.querySelector(".copy-fallback").value'),expectedPath);
      assert(await js('document.activeElement===document.querySelector(".copy-fallback")'));
    } finally { await js('navigator.clipboard.writeText=window.originalClipboardWrite;delete window.originalClipboardWrite'); }
    await click('[data-action="close-dialog"]');
    record('Denied clipboard access provides a selected manual-copy path');

    await click('[data-page="apps"]');
    assert.equal(await js('document.querySelectorAll(".file-table tbody tr").length'), 3);
    record('Installed-app demo inventory');

    let downloadResult;
    session.defaultSession.once('will-download', (_event, item) => {
      item.setSavePath(path.join(artifacts, 'exported-report.html'));
      item.once('done', (_e, status) => { downloadResult = status; });
    });
    await click('[data-action="export"]');
    await click('[data-format="html"]');
    for (let i = 0; i < 80 && !downloadResult; i++) await sleep(75);
    assert.equal(downloadResult, 'completed');
    assert.match(fs.readFileSync(path.join(artifacts, 'exported-report.html'), 'utf8'), /Fictional demo report/);
    record('Real browser HTML export');

    const reportFile=path.join(artifacts,'exported-report.html');
    const reportSession=session.fromPartition('lumen-export-test');
    reportSession.webRequest.onBeforeRequest((details,callback)=>{
      const allowed=details.url===pathToFileURL(reportFile).href;
      if(!allowed)errors.push('Unexpected exported report request: '+details.url);
      callback({cancel:!allowed});
    });
    const reportWindow=new BrowserWindow({show:false,width:1000,height:1000,webPreferences:{session:reportSession,contextIsolation:true,nodeIntegration:false,sandbox:true,offscreen:true}});
    try {
      await reportWindow.loadFile(reportFile);
      assert(await reportWindow.webContents.executeJavaScript('[...document.querySelectorAll("details li")].every(node=>node.getBoundingClientRect().height>0)'));
      const pdf=await reportWindow.webContents.printToPDF({printBackground:true,pageSize:'A4'});
      assert.equal(pdf.subarray(0,4).toString(),'%PDF');
      assert(pdf.length>10000,'Printed report appears empty');
      fs.writeFileSync(path.join(artifacts,'exported-report.pdf'),pdf);
      fs.writeFileSync(path.join(artifacts,'report-desktop.png'),(await reportWindow.webContents.capturePage()).toPNG());
    } finally { reportWindow.destroy(); }
    record('Standalone report renders locations and prints to PDF offline');

    downloadResult=undefined;
    session.defaultSession.once('will-download', (_event,item)=>{
      item.setSavePath(path.join(artifacts,'exported-inventory.csv'));
      item.once('done',(_e,status)=>{downloadResult=status;});
    });
    await click('[data-action="export"]');
    await click('[data-format="csv"]');
    for(let i=0;i<80&&!downloadResult;i++)await sleep(75);
    assert.equal(downloadResult,'completed');
    const exportedCsv=fs.readFileSync(path.join(artifacts,'exported-inventory.csv'),'utf8');
    assert.match(exportedCsv,/Last human-opened/);
    assert.match(exportedCsv,/package.json/);
    record('Real browser CSV inventory export');

    // Inject an untrusted filename into in-memory demo data to verify UI escaping.
    await js('state.report.files[0].name = "<img src=x onerror=alert(1)>"; state.report.files[0].relative = "<script>bad()</script>"; state.page="explorer"; state.query=""; state.category="all"; state.pageNumber=1; shell()');
    assert.equal(await js('Boolean(document.querySelector("#page-content img"))'), false);
    assert.equal(await js('Boolean(document.querySelector("#page-content script"))'), false);
    record('Untrusted filenames render as text');

    await js(`(async()=>{
      const originalFetch=window.fetch;
      window.fetch=async (...args)=>{const response=await originalFetch(...args);if(String(args[0]).endsWith('/demo-previous'))await new Promise(resolve=>setTimeout(resolve,180));return response;};
      try {await Promise.all([loadReport('demo-previous'),loadReport('demo-current')]);} finally {window.fetch=originalFetch;}
    })()`);
    assert.equal(await js('state.report.id'),'demo-current');
    record('Late snapshot response cannot replace a newer selection');

    await js(`(async()=>{
      const originalFetch=window.fetch;
      window.fetch=async (...args)=>{const response=await originalFetch(...args);if(String(args[0])==='/api/ask')await new Promise(resolve=>setTimeout(resolve,180));return response;};
      try {const pending=ask('Explain duplicate files');await loadReport('demo-current');await pending;} finally {window.fetch=originalFetch;}
    })()`);
    assert.equal(await js('state.messages.length'),0);
    record('Stale assistant response is discarded after snapshot reload');
    await js(`(async()=>{
      const originalApi=api;
      state.page='overview';
      api=async(path,...args)=>{if(path==='/api/history')throw new Error('Simulated unavailable database');return originalApi(path,...args);};
      try {await init();} finally {api=originalApi;}
    })()`);
    assert(await js('Boolean(document.querySelector(".hero-card"))'));
    assert.match(await js('document.querySelector("#toast").textContent'),/Saved snapshots could not be loaded/);
    await js('init()');
    record('Unavailable saved history does not prevent demo startup');

    await js(`(async()=>{
      const originalApi=api, previousScan=state.scan;
      api=async(path,...args)=>{if(path==='/api/scan')return {status:'complete',report_id:'demo-current'};if(path==='/api/history')throw new Error('Simulated history failure after scan');return originalApi(path,...args);};
      scanFailures=0;
      try {for(let i=0;i<6;i++){await pollScan();clearTimeout(scanTimer);}}
      finally {api=originalApi;state.scan=previousScan;}
    })()`);
    assert.equal(await js('scanFailures'),6);
    assert(await js('Boolean(document.querySelector("[data-action=retry-scan]"))'));
    await js('scanFailures=0;renderProgress()');
    record('Post-scan history failures stop retrying and offer reconnect');

    const performanceResult=await js(`(()=>{
      const original=state.report;
      const file=original.files[0], finding=original.findings[0], group=original.duplicates[0];
      state.report={...original,files:Array.from({length:100000},(_,i)=>({...file,id:'synthetic-'+i,name:'fixture-'+i+'.txt',path:'C:/synthetic/fixture-'+i+'.txt',relative:'fixture-'+i+'.txt',size:i+1})),findings:Array.from({length:2500},(_,i)=>({...finding,id:'synthetic-finding-'+i})),duplicates:Array.from({length:1000},(_,i)=>({...group,id:'synthetic-group-'+i,files:Array.from({length:100},(_,n)=>({...file,id:'copy-'+i+'-'+n}))}))};
      state.page='explorer';state.query='';state.category='all';state.pageNumber=1;
      const start=performance.now();shell();const first=performance.now()-start;
      state.query='fixture-999';const search=performance.now();document.querySelector('#file-results').innerHTML=fileResults();const searchMs=performance.now()-search;
      state.page='review';state.reviewKind='all';state.reviewPage=1;shell();const reviewCards=document.querySelectorAll('.review-card').length;
      state.page='duplicates';state.duplicatePage=1;shell();const groups=document.querySelectorAll('.duplicate-group').length;const copies=document.querySelectorAll('.duplicate-paths>div').length;
      state.report=original;state.query='';state.page='overview';shell();
      return {files:100000,firstRenderMs:first,searchMs,reviewCards,groups,copies};
    })()`);
    assert.equal(performanceResult.reviewCards,24);
    assert.equal(performanceResult.groups,12);
    assert.equal(performanceResult.copies,240);
    assert(performanceResult.firstRenderMs<5000,'100k file view took over 5 seconds');
    assert(performanceResult.searchMs<2000,'100k file search took over 2 seconds');
    fs.writeFileSync(path.join(artifacts,'performance.json'),JSON.stringify(performanceResult,null,2));
    record('100,000-file view and bounded review/duplicate rendering');

    await js('loadReport("demo-current")');
    await click('[data-page="overview"]');
    await js('document.querySelector("#toast").className=""');
    win.setContentSize(390, 844);
    await sleep(200);
    assert(await js('document.documentElement.scrollWidth <= window.innerWidth'), 'Mobile overview overflows horizontally');
    fs.writeFileSync(path.join(artifacts, 'overview-mobile.png'), (await win.webContents.capturePage()).toPNG());
    await click('[data-action="mobile-nav"]');
    await click('[data-page="review"]');
    assert(await js('document.documentElement.scrollWidth <= window.innerWidth'), 'Mobile review overflows horizontally');
    await click('[data-action="finding"]');
    assert(await js('document.querySelector("dialog").getBoundingClientRect().width <= window.innerWidth'));
    fs.writeFileSync(path.join(artifacts, 'evidence-mobile.png'), (await win.webContents.capturePage()).toPNG());
    await click('[data-action="close-dialog"]');
    record('390 px mobile layout, navigation, and drawer');

    const edgeViews=await js(`(()=>{
      const originalReport=state.report, originalHistory=state.history;
      state.report={...originalReport,id:'empty-fixture',files:[],findings:[],duplicates:[],apps:[],summary:{files:0,bytes:0,findings:0,review_bytes:0,duplicate_bytes:0,categories:[]}};
      const empty=[];
      for(const page of ['overview','explorer','review','duplicates','history','apps','assistant']){
        state.page=page;shell();empty.push({page,width:document.documentElement.scrollWidth,invalid:/NaN|Infinity/.test(document.querySelector('#page-content').textContent)});
      }
      state.report={...originalReport,name:'x'.repeat(80)};
      state.history=originalHistory.map(report=>report.id===state.report.id?{...report,name:state.report.name}:report);
      state.page='history';shell();const labelWidth=document.documentElement.scrollWidth;
      const clippedLabels=[...document.querySelectorAll('.snapshot-row>div>strong,.comparison-panel .panel-heading p')].filter(node=>node.scrollWidth>node.clientWidth).length;
      state.report=originalReport;state.history=originalHistory;state.page='overview';shell();
      return {empty,labelWidth,clippedLabels,width:window.innerWidth};
    })()`);
    for(const view of edgeViews.empty){assert.equal(view.invalid,false,view.page+' contains invalid numbers');assert(view.width<=edgeViews.width,view.page+' empty state overflows');}
    assert(edgeViews.labelWidth<=edgeViews.width,'Long snapshot label overflows mobile history: '+edgeViews.labelWidth);
    assert.equal(edgeViews.clippedLabels,0,'Long snapshot labels are clipped');
    record('Empty snapshots and maximum-length labels fit mobile views');

    if(process.env.LUMEN_FIXTURE_URL && process.env.LUMEN_FIXTURE_ROOT){
      session.defaultSession.webRequest.onBeforeRequest((details, callback)=>{
        const allowed=details.url.startsWith(process.env.LUMEN_FIXTURE_URL) || details.url.startsWith('blob:') || details.url.startsWith('data:');
        if(!allowed)errors.push('Unexpected network request: '+details.url);
        callback({cancel:!allowed});
      });
      win.setContentSize(1280, 900);
      await win.loadURL(process.env.LUMEN_FIXTURE_URL);
      await waitFor('Boolean(document.querySelector(".hero-card"))');
      assert.equal(await js('state.config.demo_only'), false);
      const initialLiveCount = await js('state.history.filter(r=>!r.demo).length');
      await click('[data-action="scan"]');
      assert.equal(await js('document.querySelector("#scan-roots").placeholder'),'C:\\Users\\you\\Downloads');
      await js("document.querySelector('#scan-name').value='Browser fixture snapshot'");
      await js(`document.querySelector('#scan-roots').value=${JSON.stringify(process.env.LUMEN_FIXTURE_ROOT)};document.querySelector('#scan-hash').checked=true;document.querySelector('#scan-form').requestSubmit()`);
      await waitFor('!state.report.demo');
      assert.equal(await js('state.report.summary.files'), 4);
      assert.equal(await js('state.report.name'),'Browser fixture snapshot');
      assert.equal(await js('state.report.duplicates.length'), 1);
      assert.equal(await js('state.report.coverage.apps_requested'), false);
      assert.equal(await js('state.report.files.every(f=>f.path.startsWith('+JSON.stringify(process.env.LUMEN_FIXTURE_ROOT)+'))'),true);
      record('Real scan form, job progress, and fixture-only live report');
      await click('[data-page="history"]');
      assert.equal(await js('state.history.filter(r=>!r.demo).length'), initialLiveCount + 1);
      await click('[data-page="explorer"]');
      await click('.file-link');
      assert.match(await js('document.querySelector("dialog").textContent'),/What it likely does/);
      record('Live snapshot persistence and per-file explanation');
      await click('[data-action="close-dialog"]');
      await click('[data-action="scan"]');
      await js("document.querySelector('#scan-roots').value='relative/path';document.querySelector('#scan-form').requestSubmit()");
      await waitFor('Boolean(document.querySelector("#scan-error").textContent)');
      assert.equal(await js('document.querySelector("#scan-form button[type=submit]").disabled'),false);
      record('Inline scan error and retry state');
    }

    assert.deepEqual(errors, [], 'Browser errors or external requests');
    record('No browser errors or external network requests');
    fs.writeFileSync(path.join(artifacts, 'results.json'), JSON.stringify({passed: results.length, checks: results, errors}, null, 2));
    process.stdout.write(`\n${results.length} browser checks passed. Screenshots: ${artifacts}\n`);
    win.destroy();app.exit(0);
  } catch(error) {
    process.stderr.write(error.stack + '\n');
    if(win&&!win.isDestroyed()) {try{fs.writeFileSync(path.join(artifacts, 'failure.png'), (await win.webContents.capturePage()).toPNG());}catch{} win.destroy();}
    app.exit(1);
  }
});

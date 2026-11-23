// Bring an existing Electron binary; this runner installs nothing.
// node tests/run-browser.cjs --electron C:/path/to/electron.exe
const {spawn}=require('node:child_process');
const path=require('node:path');
const readline=require('node:readline');
const electron=process.env.LUMEN_ELECTRON_PATH || process.argv[process.argv.indexOf('--electron')+1];
if(!electron || electron===process.argv[0])throw Error('Pass --electron with an existing Electron executable path.');
const root=path.resolve(__dirname,'..');
const env=Object.fromEntries(Object.entries(process.env).filter(([key])=>key.toUpperCase()!=='ELECTRON_RUN_AS_NODE'));
const fixture=spawn(process.env.LUMEN_PYTHON || 'python',[path.join(__dirname,'ui_fixture_server.py')],{cwd:root,windowsHide:true,stdio:['pipe','pipe','inherit']});
let browser,finished=false;
function finish(code){if(finished)return;finished=true;clearTimeout(watchdog);fixture.stdin.end();if(browser&&!browser.killed)browser.kill();fixture.once('exit',()=>process.exit(code));setTimeout(()=>{fixture.kill();process.exit(code);},4000).unref();}
const watchdog=setTimeout(()=>{console.error('Browser checks timed out.');finish(1);},120000);
fixture.on('error',error=>{console.error(error.message);finish(1);});
fixture.on('exit',code=>{if(!finished){console.error('Fixture server exited unexpectedly:',code);finish(1);}});
readline.createInterface({input:fixture.stdout}).once('line',line=>{
  try {
    const data=JSON.parse(line);
    Object.assign(env,{LUMEN_TEST_URL:data.demo,LUMEN_FIXTURE_URL:data.live,LUMEN_FIXTURE_ROOT:data.root});
    browser=spawn(electron,[path.join(__dirname,'ui-smoke.cjs')],{cwd:root,windowsHide:true,stdio:'inherit',env});
    browser.on('error',error=>{console.error(error.message);finish(1);});
    browser.on('exit',code=>finish(code??1));
  }catch(error){console.error(error.message);finish(1);}
});
process.on('SIGINT',()=>finish(130));

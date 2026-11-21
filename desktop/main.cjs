'use strict';
const {app,BaseWindow,WebContentsView,session,ipcMain,shell,dialog,Menu}=require('electron');
const {spawn}=require('node:child_process');
const {randomBytes}=require('node:crypto');
const net=require('node:net');
const path=require('node:path');
const fs=require('node:fs');
const os=require('node:os');
const {PROVIDERS,publicHttps,allowedTopLevel,isLocalApp,layout}=require('./policy.cjs');

app.setName('SuxenAI');
const selfTest=process.argv.includes('--self-test');
if(selfTest||process.env.SUXENAI_DESKTOP_PROFILE){const dir=process.env.SUXENAI_DESKTOP_PROFILE||fs.mkdtempSync(path.join(os.tmpdir(),'suxenai-desktop-test-'));fs.mkdirSync(dir,{recursive:true});app.setPath('userData',dir);}
let win,local,backend,origin,token,stopping=false;
const pool=new Map(),slots=[null,null],errors=new Map();
const localPartition='persist:suxenai-workspace';
const preferences={nodeIntegration:false,contextIsolation:true,sandbox:true,webSecurity:true,allowRunningInsecureContent:false};

function availablePort(){return new Promise((resolve,reject)=>{const s=net.createServer();s.on('error',reject);s.listen(0,'127.0.0.1',()=>{const port=s.address().port;s.close(()=>resolve(port));});});}
async function startBackend(){
  const port=await availablePort();origin=`http://127.0.0.1:${port}`;token=randomBytes(32).toString('hex');
  const data=process.env.SUXENAI_DATA_DIR||app.getPath('userData');
  fs.mkdirSync(data,{recursive:true});
  const env={...process.env,SUXENAI_PORT:String(port),SUXENAI_DATA_DIR:data,SUXENAI_DESKTOP_TOKEN:token};
  const executable=path.join(process.resourcesPath,'backend',process.platform==='win32'?'backend.exe':'backend');
  const source=path.resolve(__dirname,'..','server.py');
  const command=app.isPackaged?executable:(process.env.SUXENAI_PYTHON||'python3');
  const args=app.isPackaged?[]:[source];
  backend=spawn(command,args,{env,stdio:'ignore',windowsHide:true});
  let exited=false;backend.on('error',()=>{exited=true;});backend.on('exit',()=>{exited=true;if(!stopping&&win&&!win.isDestroyed())dialog.showErrorBox('SuxenAI','Le serveur local s’est arrêté. Fermez et relancez SuxenAI.');});
  for(let i=0;i<100&&!exited;i++){
    try{const r=await fetch(origin+'/api/health',{headers:{'X-SuxenAI-Desktop':token},signal:AbortSignal.timeout(800)});if(r.ok&&(await r.json()).app==='SuxenAI')return;}catch{}
    await new Promise(resolve=>setTimeout(resolve,100));
  }
  throw Error('Impossible de démarrer le serveur local.');
}

function sendState(){if(local&&!local.webContents.isDestroyed())local.webContents.send('desktop:state-changed',state());}
function state(){return slots.map(id=>{if(!id)return null;let domain=PROVIDERS[id].url;try{const url=new URL(pool.get(id)?.webContents.getURL());if(url.protocol==='https:')domain=url.origin;}catch{}return {id,name:PROVIDERS[id].name,domain,error:errors.get(id)||''};});}
function refreshLayout(){
  if(!win||win.isDestroyed())return;
  const active=slots.filter(Boolean),minWidth=active.length===2?1120:930;
  win.setMinimumSize(minWidth,650);let {width,height}=win.getContentBounds();if(width<minWidth){win.setContentSize(minWidth,height);width=minWidth;}
  const bounds=layout(width,height,active.length);
  local.setBounds(bounds.local);
  let index=0;for(const id of active){const view=pool.get(id);view.setBounds(bounds.remote[index++]);}
}
function hideSlot(slot){const id=slots[slot];if(id){const view=pool.get(id);try{win.contentView.removeChildView(view);}catch{}slots[slot]=null;}}
function getProviderView(id){
  if(pool.has(id))return pool.get(id);
  // Each provider has its own durable Chromium profile; no preload or shared session.
  const partition='persist:suxenai-provider-'+id,ses=session.fromPartition(partition);
  ses.setPermissionRequestHandler((_wc,_permission,callback)=>callback(false));
  ses.setPermissionCheckHandler(()=>false);
  ses.webRequest.onBeforeRequest({urls:['<all_urls>']},(details,callback)=>{
    let allowed=publicHttps(details.url,true);
    if(details.resourceType==='mainFrame')allowed=allowedTopLevel(id,details.url);
    // Remote sites may use their own blob/data resources, never local files or loopback HTTP.
    if(details.resourceType!=='mainFrame'&&/^(blob:|data:)/.test(details.url))allowed=true;
    callback({cancel:!allowed});
  });
  ses.on('will-download',(event)=>{event.preventDefault();errors.set(id,'Téléchargement Web désactivé ici. Utilisez le navigateur externe.');sendState();});
  const view=new WebContentsView({webPreferences:{...preferences,partition}}),wc=view.webContents;
  wc.setWindowOpenHandler(()=>{errors.set(id,'Fenêtre supplémentaire bloquée. Si nécessaire, connectez-vous dans le navigateur externe.');sendState();return {action:'deny'};});
  wc.on('will-navigate',(event,url)=>{if(!allowedTopLevel(id,event.url||url)){event.preventDefault();errors.set(id,'Navigation externe bloquée. Ouvrez le site dans le navigateur si nécessaire.');sendState();}});
  wc.on('will-redirect',(event,url)=>{if(event.isMainFrame!==false&&!allowedTopLevel(id,event.url||url)){event.preventDefault();errors.set(id,'Redirection externe bloquée. Utilisez le navigateur externe.');sendState();}});
  wc.on('did-navigate',()=>{errors.delete(id);sendState();});
  wc.on('did-navigate-in-page',()=>sendState());
  wc.on('did-fail-load',(_event,code,_description,_url,isMainFrame)=>{if(isMainFrame&&code!==-3){errors.set(id,'Page inaccessible dans Chromium intégré. Utilisez le navigateur externe.');sendState();}});
  wc.on('render-process-gone',()=>{errors.set(id,'Onglet arrêté. Rechargez ou ouvrez le navigateur externe.');sendState();});
  pool.set(id,view);wc.loadURL(PROVIDERS[id].url).catch(()=>{});return view;
}
function openProvider(id,slot){
  if(!Object.hasOwn(PROVIDERS,id)||![0,1].includes(slot))throw Error('Onglet invalide.');
  if(slot===1&&!slots[0])slot=0;
  const current=slots.indexOf(id);if(current>=0&&current!==slot)return state();
  if(slots[slot]!==id){hideSlot(slot);const view=getProviderView(id);slots[slot]=id;win.contentView.addChildView(view);}
  refreshLayout();sendState();return state();
}
function trusted(event){return local&&event.sender===local.webContents&&event.senderFrame&&isLocalApp(event.senderFrame.url,origin);}
function handle(name,fn){ipcMain.handle('desktop:'+name,(event,...args)=>{if(!trusted(event))throw Error('Accès refusé.');return fn(...args);});}
function slotView(slot){if(![0,1].includes(slot)||!slots[slot])throw Error('Onglet fermé.');return pool.get(slots[slot]).webContents;}
function setupIPC(){
  handle('open',openProvider);handle('close',slot=>{if(![0,1].includes(slot))throw Error('Onglet invalide');hideSlot(slot);if(!slots[0]&&slots[1]){slots[0]=slots[1];slots[1]=null;}refreshLayout();sendState();return state();});
  handle('reload',slot=>{slotView(slot).reload();return true;});handle('back',slot=>{const wc=slotView(slot);if(wc.navigationHistory.canGoBack())wc.navigationHistory.goBack();return true;});
  handle('external',id=>{if(!Object.hasOwn(PROVIDERS,id))throw Error('Service inconnu');return shell.openExternal(PROVIDERS[id].url);});handle('state',state);
}
async function setupWindow(show=true){
  const ses=session.fromPartition(localPartition);
  ses.webRequest.onBeforeRequest({urls:['<all_urls>']},(details,cb)=>cb({cancel:!isLocalApp(details.url,origin)&&!/^blob:|^data:/.test(details.url)}));
  ses.webRequest.onBeforeSendHeaders({urls:['http://127.0.0.1/*']},(details,callback)=>{const headers={...details.requestHeaders};if(isLocalApp(details.url,origin))headers['X-SuxenAI-Desktop']=token;callback({requestHeaders:headers});});
  ses.setPermissionRequestHandler((_wc,p,cb)=>cb(p==='clipboard-sanitized-write'));
  win=new BaseWindow({width:1440,height:900,minWidth:930,minHeight:650,backgroundColor:'#111214',title:'SuxenAI · Chromium',show});
  local=new WebContentsView({webPreferences:{...preferences,partition:localPartition,preload:path.join(__dirname,'preload.cjs')}});
  const wc=local.webContents;
  wc.on('will-navigate',(event,url)=>{if(!isLocalApp(event.url||url,origin))event.preventDefault();});
  wc.setWindowOpenHandler(({url})=>{if(publicHttps(url))shell.openExternal(url).catch(()=>{});return {action:'deny'};});
  win.contentView.addChildView(local);win.on('resize',refreshLayout);win.on('closed',()=>{stopping=true;for(const view of pool.values())if(!view.webContents.isDestroyed())view.webContents.close();if(!wc.isDestroyed())wc.close();backend?.kill();app.quit();});
  setupIPC();refreshLayout();wc.on('did-finish-load',sendState);await wc.loadURL(origin);
  Menu.setApplicationMenu(Menu.buildFromTemplate([{label:'SuxenAI',submenu:[{role:'quit'}]},{label:'Édition',submenu:[{role:'copy'},{role:'paste'},{role:'selectAll'}]},{label:'Affichage',submenu:[{role:'togglefullscreen'},{role:'zoomIn'},{role:'zoomOut'},{role:'resetZoom'}]}]));
}

if(!app.requestSingleInstanceLock()){app.quit();}else{
  app.on('second-instance',()=>{if(win&&!win.isDestroyed())win.focus();});
  app.on('before-quit',()=>{stopping=true;backend?.kill();});
  app.whenReady().then(async()=>{
    try{await startBackend();if(selfTest){const denied=await fetch(origin+'/api/health');if(denied.status!==403)throw Error('Backend non protégé');await setupWindow(false);const ready=await local.webContents.executeJavaScript('Boolean(window.suxenDesktop && document.getElementById("webWorkspace"))');if(!ready)throw Error('Interface Chromium non chargée');backend.kill();app.exit(0);return;}await setupWindow();}
    catch(e){if(selfTest){backend?.kill();console.error(e.message);app.exit(1);return;}dialog.showErrorBox('SuxenAI',String(e.message||e));app.quit();}
  });
}

'use strict';
const {contextBridge,ipcRenderer}=require('electron');
// This preload is attached exclusively to the authenticated loopback workspace.
// Provider views do not receive it or any other preload.
contextBridge.exposeInMainWorld('suxenDesktop',Object.freeze({
  open:(provider,slot=0)=>ipcRenderer.invoke('desktop:open',provider,slot),
  close:slot=>ipcRenderer.invoke('desktop:close',slot),
  reload:slot=>ipcRenderer.invoke('desktop:reload',slot),
  back:slot=>ipcRenderer.invoke('desktop:back',slot),
  external:provider=>ipcRenderer.invoke('desktop:external',provider),
  state:()=>ipcRenderer.invoke('desktop:state'),
  onState:callback=>{ipcRenderer.on('desktop:state-changed',(_event,state)=>callback(state));}
}));

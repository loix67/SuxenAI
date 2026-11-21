'use strict';

const net = require('node:net');
const PROVIDERS = Object.freeze({
  chatgpt: { name: 'ChatGPT', url: 'https://chatgpt.com/', hosts: ['chatgpt.com','openai.com'] },
  claude: { name: 'Claude', url: 'https://claude.ai/', hosts: ['claude.ai','anthropic.com'] },
  gemini: { name: 'Gemini', url: 'https://gemini.google.com/', hosts: ['gemini.google.com','accounts.google.com'] },
  mistral: { name: 'Le Chat', url: 'https://chat.mistral.ai/', hosts: ['mistral.ai'] }
});

function publicHttps(raw, websocket=false) {
  try {
    const url=new URL(raw), host=url.hostname.toLowerCase().replace(/\.$/,'');
    return (url.protocol==='https:'||(websocket&&url.protocol==='wss:')) && !url.username && !url.password &&
      !!host.includes('.') && !net.isIP(host) && !host.endsWith('.localhost') && !host.endsWith('.local') &&
      !host.endsWith('.internal') && !host.endsWith('.lan') && !host.endsWith('.home');
  } catch { return false; }
}

function allowedTopLevel(provider,raw) {
  if (!Object.hasOwn(PROVIDERS,provider)||!publicHttps(raw)) return false;
  const host=new URL(raw).hostname.toLowerCase().replace(/\.$/,'');
  // Keep navigation within provider-owned sites and explicit, common identity endpoints.
  const hosts=[...PROVIDERS[provider].hosts,'accounts.google.com','login.microsoftonline.com','appleid.apple.com','github.com'];
  return hosts.some(h=>host===h||host.endsWith('.'+h));
}

function isLocalApp(raw,origin) {
  try {return new URL(raw).origin===origin;} catch {return false;}
}

function layout(width,height,count){
  if(count===0)return {local:{x:0,y:0,width,height},remote:[]};
  const localWidth=Math.min(Math.max(410,Math.floor(width*(count===1?0.45:0.34))),width-350*count);
  const safeWidth=Math.max(1,localWidth),remaining=width-safeWidth;
  const remote=[];let x=safeWidth;
  for(let i=0;i<count;i++){const w=i===count-1?width-x:Math.floor(remaining/count);remote.push({x,y:0,width:w,height});x+=w;}
  return {local:{x:0,y:0,width:safeWidth,height},remote};
}

module.exports={PROVIDERS,publicHttps,allowedTopLevel,isLocalApp,layout};

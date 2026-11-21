'use strict';
const path=require('node:path');
const fs=require('node:fs');

function fixBackendLinks(original,copied){
  // Packager's extraResource copy resolves source links to absolute paths on macOS.
  // Rebase only links within this generated backend to make the app portable.
  for(const entry of fs.readdirSync(copied,{withFileTypes:true})){
    const filename=path.join(copied,entry.name);
    if(entry.isDirectory())fixBackendLinks(original,filename);
    else if(entry.isSymbolicLink()){
      const target=fs.readlinkSync(filename);if(!path.isAbsolute(target))continue;
      const rel=path.relative(original,target);if(rel==='..'||rel.startsWith('..'+path.sep)||path.isAbsolute(rel))throw Error('Lien externe dans le backend');
      // Determine the copied backend root from the location of this link.
      let root=copied;while(path.basename(root)!=='backend'){const parent=path.dirname(root);if(parent===root)throw Error('Dossier backend absent');root=parent;}
      fs.unlinkSync(filename);fs.symlinkSync(path.relative(path.dirname(filename),path.join(root,rel)),filename);
    }
  }
}

(async()=>{
  const mod=await import('@electron/packager');
  const packager=mod.packager||mod.default;
  const root=path.resolve(__dirname,'..'),backend=path.join(root,'desktop-build','backend');
  if(!fs.existsSync(backend))throw Error('Compiler d’abord le backend (voir README).');
  const result=await packager({dir:__dirname,name:'SuxenAI',appBundleId:'org.suxenai.desktop',appVersion:'1.1.0',electronVersion:'45.4.1',platform:process.platform,arch:process.arch,out:process.env.SUXENAI_DESKTOP_OUT||path.join(root,'desktop-release'),overwrite:true,asar:true,extraResource:[backend],ignore:[/^\/node_modules($|\/)/,/^\/tests($|\/)/,/^\/pnpm-lock\.yaml$/,/^\/pnpm-workspace\.yaml$/],osxSign:false,...(process.env.SUXENAI_ELECTRON_ZIP_DIR?{electronZipDir:process.env.SUXENAI_ELECTRON_ZIP_DIR}:{})});
  if(process.platform==='darwin')for(const output of result)fixBackendLinks(backend,path.join(output,'SuxenAI.app','Contents','Resources','backend'));
  console.log(result.join('\n'));
})().catch(e=>{console.error(e.message);process.exitCode=1;});

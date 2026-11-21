const $=id=>document.getElementById(id);let state={projects:[],chats:[],agents:[],providers:[]},projectId=null,chatId=null,busy=false;
async function api(path,data){const res=await fetch('/api/'+path,{method:data===undefined?'GET':'POST',headers:{'Content-Type':'application/json'},body:data===undefined?undefined:JSON.stringify(data)});const json=await res.json();if(!res.ok)throw Error(json.error||'Erreur réseau');return json}
function toast(m){$('toast').textContent=m;$('toast').classList.add('show');setTimeout(()=>$('toast').classList.remove('show'),3800)}
function el(tag,cls,text){const e=document.createElement(tag);if(cls)e.className=cls;if(text!==undefined)e.textContent=text;return e}
function nav(root,items,selected,icon,onClick){root.replaceChildren();items.forEach(item=>{const b=el('button','navitem'+(selected===item.id?' active':''));b.append(el('span','symbol',icon),el('span','',item.name||item.title));b.onclick=()=>onClick(item.id);root.append(b)})}
function activeChat(){return state.chats.find(c=>c.id===chatId)}
function activeProject(){return state.projects.find(p=>p.id===projectId)}
function members(){return state.agents.filter(a=>a.chat===chatId)}
async function refresh(preserve=true){const oldP=projectId,oldC=chatId;state=await api('state');projectId=(preserve&&state.projects.some(p=>p.id===oldP)?oldP:state.projects[0]?.id)||null;chatId=(preserve&&state.chats.some(c=>c.id===oldC&&c.project===projectId)?oldC:state.chats.find(c=>c.project===projectId)?.id)||null;render()}
function render(){nav($('projects'),state.projects,projectId,'◈',id=>{projectId=id;chatId=state.chats.find(c=>c.project===id)?.id||null;render()});nav($('chats'),state.chats.filter(c=>c.project===projectId),chatId,'⌁',id=>{chatId=id;render()});const p=activeProject(),c=activeChat();$('projectName').textContent=p?.name||'Sans projet';$('repoName').textContent=p?.repo||'Aucun dépôt associé';$('chatTitle').textContent=c?.title||'Nouvelle discussion';const me=members();$('agents').replaceChildren();for(const a of me){const item=el('div','agent');item.append(el('span','agent-icon',a.name.slice(0,2).toUpperCase()));const info=el('div','agent-info');info.append(el('strong','',a.name),el('small','',(a.role||'Sans rôle')+' · '+a.provider));item.append(info);const btn=el('button','',a.enabled?'●':'○');btn.title='Activer / désactiver';btn.onclick=()=>changeAgent(a);item.append(btn);const edit=el('button','','✎');edit.title='Modifier';edit.onclick=()=>editAgent(a);item.append(edit);$('agents').append(item)}const coordinator=$('coordinator');coordinator.replaceChildren(new Option('Aucun coordinateur',''));for(const a of me)coordinator.add(new Option(a.name,a.id));if(c){document.querySelectorAll('[data-mode]').forEach(b=>b.classList.toggle('selected',b.dataset.mode===c.mode));coordinator.value=c.coordinator||'';$('coordWrap').hidden=c.mode!=='coordinated';setModeHint(c.mode)}loadMessages()}
function setModeHint(mode){const d={free:'Échange libre entre tous les participants.',targeted:'Les IA mentionnées uniquement répondent.',coordinated:'Le coordinateur intervient en premier.'};$('modeHint').textContent=d[mode]||d.free;$('modeDescription').textContent=d[mode]||d.free}
async function loadMessages(){if(!chatId){$('messages').replaceChildren();$('intro').hidden=false;return}try{const out=await api('messages?chat='+encodeURIComponent(chatId));$('messages').replaceChildren();$('intro').hidden=out.messages.length>0;for(const m of out.messages){const mine=m.speaker==='Vous';const item=el('div','msg'+(mine?' you':''));item.append(el('div','avatar',mine?'VO':m.speaker.slice(0,2).toUpperCase()));const bubble=el('div','bubble');bubble.append(el('div','speaker',m.speaker),el('div','content',m.content));item.append(bubble);$('messages').append(item)}$('messages').scrollTop=$('messages').scrollHeight}catch(e){toast(e.message)}}
function openDialog(title,fields,save){$('dialogTitle').textContent=title;$('dialogFields').replaceChildren();for(const f of fields){const wrapper=el('div','form-field');const label=el('label','',f.label);label.htmlFor='f_'+f.key;wrapper.append(label);let input;if(f.type==='textarea'){input=el('textarea','field');input.rows=4}else if(f.type==='select'){input=el('select','field');for(const [value,text] of f.options)input.add(new Option(text,value))}else{input=el('input','field');input.type='text'}input.id='f_'+f.key;input.value=f.value||'';wrapper.append(input);$('dialogFields').append(wrapper)}$('dialog').showModal();const form=$('dialogForm');form.onsubmit=async e=>{e.preventDefault();const data={};for(const f of fields)data[f.key]=$('f_'+f.key).value;try{await save(data);$('dialog').close();await refresh()}catch(err){toast(err.message)}}}
$('addProject').onclick=()=>openDialog('Nouveau projet',[{key:'name',label:'Nom du projet'},{key:'repo',label:'URL GitHub (facultative)'},{key:'instructions',label:'Instructions communes',type:'textarea'}],async d=>{const r=await api('projects',d);projectId=r.id;chatId=null});
$('editProject').onclick=$('settings').onclick=()=>{const p=activeProject();if(!p)return;openDialog('Configurer le projet',[{key:'name',label:'Nom',value:p.name},{key:'repo',label:'URL GitHub (référence)',value:p.repo},{key:'instructions',label:'Instructions',type:'textarea',value:p.instructions}],d=>api('projects/update',{id:projectId,...d}))};
$('addChat').onclick=async()=>{if(!projectId)return;try{const r=await api('chats',{project:projectId,title:'Nouvelle discussion'});chatId=r.id;await refresh()}catch(e){toast(e.message)}};
$('branch').onclick=async()=>{if(!chatId)return;try{const r=await api('chats/branch',{chat:chatId});chatId=r.id;await refresh();toast('Branche créée')}catch(e){toast(e.message)}};
$('addAgent').onclick=()=>{if(!chatId)return toast('Crée d’abord une discussion');openDialog('Inviter une IA',[{key:'name',label:'Nom du participant'},{key:'provider',label:'Fournisseur',type:'select',options:state.providers.map(p=>[p.id,p.id+(p.available?'':' · clé requise')])},{key:'model',label:'Nom du modèle (facultatif)'},{key:'role',label:'Spécialité facultative'}],d=>api('agents',{chat:chatId,...d}))};
function editAgent(a){openDialog('Modifier '+a.name,[{key:'name',label:'Nom',value:a.name},{key:'provider',label:'Fournisseur',type:'select',value:a.provider,options:state.providers.map(p=>[p.id,p.id])},{key:'model',label:'Modèle',value:a.model},{key:'role',label:'Rôle facultatif',value:a.role}],d=>api('agents/update',{...d,id:a.id,enabled:!!a.enabled}))}
async function changeAgent(a){try{await api('agents/update',{...a,enabled:!a.enabled});await refresh()}catch(e){toast(e.message)}}
document.querySelectorAll('[data-mode]').forEach(b=>b.onclick=async()=>{try{await api('chats/update',{id:chatId,mode:b.dataset.mode,coordinator:$('coordinator').value});await refresh()}catch(e){toast(e.message)}});
$('coordinator').onchange=async()=>{const ch=activeChat();try{await api('chats/update',{id:chatId,mode:ch.mode,coordinator:$('coordinator').value});await refresh()}catch(e){toast(e.message)}};
async function teamRun(targets){if(busy||!chatId)return;busy=true;$('send').disabled=$('runRound').disabled=true;$('sendingStatus').textContent='Les IA collaborent…';try{const out=await api('round',{chat:chatId,targets,rounds:Number($('rounds').value)});await loadMessages();const errors=out.results.filter(x=>!x.ok);if(errors.length)toast(errors.map(x=>x.speaker+' : '+x.error).join(' | ').slice(0,500))}catch(e){toast(e.message)}finally{busy=false;$('send').disabled=$('runRound').disabled=false;$('sendingStatus').textContent=''}}
$('send').onclick=async()=>{const content=$('input').value.trim();if(!content||busy||!chatId)return;const targets=[...content.matchAll(/@([\wÀ-ÿ-]+)/g)].map(x=>x[1].toLowerCase());try{await api('messages',{chat:chatId,content});$('input').value='';await loadMessages();const ch=activeChat();const selected=members().filter(a=>targets.includes(a.name.toLowerCase()));if(ch.mode==='targeted'&&!selected.length){toast('Mentionne @Nom pour sélectionner une IA');return}await teamRun(selected.length?selected.map(a=>a.id):null)}catch(e){toast(e.message)}};
$('input').onkeydown=e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();$('send').click()}};
$('runRound').onclick=()=>teamRun();
$('exportChat').onclick=async()=>{if(!chatId)return;try{const data=await api('export?chat='+encodeURIComponent(chatId));const url=URL.createObjectURL(new Blob([JSON.stringify(data,null,2)],{type:'application/json'}));const link=el('a');link.href=url;link.download='suxenai-discussion.json';link.click();setTimeout(()=>URL.revokeObjectURL(url),1000)}catch(e){toast(e.message)}};
$('menu').onclick=()=>$('projects').closest('.sidebar').classList.toggle('open');

// GitHub project explorer: explicit, read-only file selection.
let repositoryCache=[], repositoryLoadedFor=null;
function repoUiReset(){
  $('repoFileList').replaceChildren();
  $('attachedList').replaceChildren();
  $('repoNotice').textContent=activeProject()?.repo
    ? 'Clique sur ↻ pour consulter le dépôt.'
    : 'Ajoute une URL GitHub aux paramètres du projet.';
}
async function attachedFiles(){
  if(!projectId)return;
  const pid=projectId;
  try{
    const data=await api('repository/attached?project='+encodeURIComponent(pid));
    if(pid!==projectId)return;
    $('attachedList').replaceChildren();
    if(!data.files.length)return;
    $('attachedList').append(el('div','file-subheading','FICHIERS PARTAGÉS AVEC LES IA'));
    for(const f of data.files){
      const row=el('div','repo-item');
      row.append(el('span','file-name',f.path));
      const b=el('button','file-button','Retirer');b.title='Retirer du contexte partagé';
      b.onclick=async()=>{try{await api('repository/detach',{project:pid,path:f.path});await attachedFiles();toast('Fichier retiré du contexte')}catch(e){toast(e.message)}};
      row.append(b);$('attachedList').append(row);
    }
  }catch(e){toast(e.message)}
}
function showRepositoryFiles(files){
  const root=$('repoFileList');root.replaceChildren();
  const search=el('input','field repo-search');
  search.placeholder='Filtrer les fichiers…';search.setAttribute('aria-label','Filtrer les fichiers GitHub');
  const entries=el('div','repo-entries');
  function draw(){
    const term=search.value.toLowerCase().trim();
    const subset=files.filter(f=>f.path.toLowerCase().includes(term)).slice(0,60);
    entries.replaceChildren();
    for(const f of subset){
      const row=el('div','repo-item');
      row.append(el('span','file-name',f.path));
      const b=el('button','file-button','Voir');
      b.onclick=()=>previewRepoFile(f.path);
      row.append(b);entries.append(row);
    }
    if(files.length>60)entries.append(el('small','repo-trunc','60 résultats maximum affichés. Utilise le filtre.'));
    if(!subset.length)entries.append(el('small','repo-trunc','Aucun fichier trouvé.'));
  }
  search.oninput=draw;root.append(search,entries);draw();
}
async function previewRepoFile(path){
  if(!projectId)return;
  const pid=projectId;
  try{
    const result=await api('repository/preview?project='+encodeURIComponent(pid)+'&path='+encodeURIComponent(path));
    if(pid!==projectId)return;
    const d=document.createElement('dialog');d.className='preview-dialog';
    const body=el('div','preview-body');
    body.append(el('div','preview-path',result.path+' · '+result.bytes+' octets'));
    const pre=el('pre','preview-code',result.content);body.append(pre);
    const actions=el('div','preview-actions');
    const cancel=el('button','ghost','Fermer');cancel.onclick=()=>d.close();
    const attach=el('button','primary','Partager avec les IA');
    attach.onclick=async()=>{attach.disabled=true;try{await api('repository/attach',{project:pid,path});d.close();await attachedFiles();toast('Fichier partagé avec les participants du projet')}catch(e){toast(e.message)}finally{attach.disabled=false}};
    actions.append(cancel,attach);body.append(actions);d.append(body);document.body.append(d);
    d.onclose=()=>d.remove();d.showModal();
  }catch(e){toast(e.message)}
}
$('refreshRepo').onclick=async()=>{
  if(!projectId||!activeProject()?.repo)return toast('Configure d’abord une URL GitHub');
  const pid=projectId;
  $('repoNotice').textContent='Lecture du dépôt GitHub…';
  try{
    const info=await api('repository/tree?project='+encodeURIComponent(pid));
    if(pid!==projectId)return;
    repositoryLoadedFor=pid;repositoryCache=info.files;
    $('repoNotice').textContent=info.repository.name+' · '+info.repository.branch+' · '+info.files.length+' fichiers';
    showRepositoryFiles(info.files);await attachedFiles();
  }catch(e){$('repoNotice').textContent=e.message;toast(e.message)}
};
const renderOriginal=render;
render=function(){
  renderOriginal();
  if(repositoryLoadedFor!==projectId){repositoryLoadedFor=null;repositoryCache=[];repoUiReset();}
  attachedFiles();
};

refresh(false).catch(e=>toast(e.message));
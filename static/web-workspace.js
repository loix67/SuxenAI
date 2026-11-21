(() => {
  let mode=null, activeProjectId=null, activeChatId=null, switching=false;
  const descriptions={web:'Web · vos abonnements, copier-coller manuel, aucun appel API',api:'API · les IA collaborent automatiquement, appels éventuellement facturés',local:'Local · modèles Ollama sur cet ordinateur, gratuit'};
  const accents={chatgpt:'GPT',claude:'CL',gemini:'GE',mistral:'ML'};
  const modeButtons=[...document.querySelectorAll('[data-execution]')];
  function showMode(next){
    mode=next;document.body.dataset.execution=next;
    $('webWorkspace').hidden=next!=='web';$('executionStatus').textContent=descriptions[next]||'';$('executionStatus').dataset.mode=next||'';workbenchVisibility();
    $('newProposal').disabled=$('newBatch').disabled=next==='web';
    $('newProposal').title=$('newBatch').title=next==='web'?'Passez en mode API ou Local pour proposer du code':'Demander une modification';
    for(const button of modeButtons){const on=button.dataset.execution===next;button.classList.toggle('active',on);button.setAttribute('aria-pressed',String(on));}
  }
  function workbenchVisibility(){$('workbenchPanel').hidden=mode==='web'||!activeProject()?.repo;}
  function clearDrafts(){for(const id of ['webPrompt','webPreview','webResponse'])$(id).value='';$('webPreview').hidden=true;$('webCopy').disabled=true;$('webIncludeHistory').checked=false;}
  async function syncMode(){
    const pid=projectId,cid=chatId;if(!pid){showMode(null);return;}
    if(activeChatId!==cid||activeProjectId!==pid){clearDrafts();activeChatId=cid;activeProjectId=pid;}
    try{const p=await api('v9/preferences?project='+encodeURIComponent(pid));if(pid===projectId&&cid===chatId&&!switching)showMode(p.mode||'web');}catch(e){toast(e.message);}
  }
  for(const button of modeButtons)button.onclick=async()=>{
    if(!projectId||switching)return;if(busy)return toast('Attendez la fin du tour en cours.');const pid=projectId,next=button.dataset.execution;
    if(next==='api'&&mode!=='api'&&!confirm('Activer les modèles API pour ce projet ? Les appels peuvent être facturés.'))return;
    switching=true;for(const b of modeButtons)b.disabled=true;
    try{await api('v10/mode',{project:pid,mode:next});if(pid===projectId)showMode(next);await refresh();}
    catch(e){toast(e.message);}finally{switching=false;for(const b of modeButtons)b.disabled=false;syncMode();}
  };
  async function providers(){
    const data=await api('v10/web/providers'),root=$('webProviders'),select=$('webResponseProvider');root.replaceChildren();select.replaceChildren();
    for(const p of data.providers){const a=el('a','web-provider');a.dataset.provider=p.id;a.href=p.url;a.target='_blank';a.rel='noopener noreferrer';a.append(el('span','provider-glyph',accents[p.id]||'AI'));const text=el('span','provider-text');text.append(el('strong','',p.name),el('small','',window.suxenDesktop?'Ouvrir dans la fenêtre':'Ouvrir le site'));a.append(text,el('span','provider-arrow','↗'));if(window.suxenDesktop)a.onclick=e=>{e.preventDefault();window.suxenDesktop.open(p.id,window.suxenSelectedSlot||0).catch(err=>toast(err.message));};root.append(a);select.add(new Option(p.name,p.id));}
  }
  async function action(button,fn){if(!chatId)return toast('Créez une discussion d’abord');button.disabled=true;try{await fn(chatId);}catch(e){toast(e.message);}finally{button.disabled=false;}}
  $('webPrepare').onclick=()=>action($('webPrepare'),async cid=>{const draft=$('webPrompt').value,history=$('webIncludeHistory').checked;const data=await api('v10/web/prepare',{chat:cid,text:draft,include_history:history});if(cid!==chatId||draft!==$('webPrompt').value||history!==$('webIncludeHistory').checked)return;$('webPreview').value=data.prompt;$('webPreview').hidden=false;$('webCopy').disabled=false;toast('Vérifiez le contenu avant de le copier.');});
  $('webPrompt').oninput=$('webIncludeHistory').onchange=()=>{$('webPreview').hidden=true;$('webPreview').value='';$('webCopy').disabled=true;};
  $('webCopy').onclick=async()=>{const preview=$('webPreview');try{await navigator.clipboard.writeText(preview.value);toast('Demande copiée. Collez-la sur le site de votre IA.');}catch{preview.focus();preview.select();toast('Copiez le texte sélectionné (⌘ C).');}};
  $('webSaveQuestion').onclick=()=>action($('webSaveQuestion'),async cid=>{const content=$('webPrompt').value.trim();if(!content)throw Error('Saisissez une demande.');await api('messages',{chat:cid,content});if(cid===chatId){await loadMessages();toast('Question enregistrée localement.');}});
  $('webImportResponse').onclick=()=>action($('webImportResponse'),async cid=>{await api('v10/web/response',{chat:cid,provider:$('webResponseProvider').value,content:$('webResponse').value});if(cid===chatId){$('webResponse').value='';await loadMessages();toast('Réponse Web importée dans la discussion.');}});
  const oldRender=render;render=function(){oldRender();workbenchVisibility();syncMode();};
  providers().catch(e=>toast(e.message));syncMode();
})();

(() => {
  const providers = [
    ['openai','OpenAI','ChatGPT et modèles GPT','https://platform.openai.com/api-keys'],
    ['anthropic','Anthropic','Claude','https://console.anthropic.com/settings/keys'],
    ['mistral','Mistral AI','Modèles Mistral','https://console.mistral.ai/api-keys'],
    ['gemini','Google Gemini','Modèles Gemini','https://aistudio.google.com/apikey'],
    ['github','GitHub','Dépôts privés et pull requests','https://github.com/settings/personal-access-tokens/new'],
    ['ollama','Ollama','IA locale, aucune clé nécessaire','https://ollama.com/'],
  ];
  const dialog=$('connectionsDialog');
  let status={},detectOnOpen=false;
  function setResult(node,message,kind=''){node.textContent=message;node.dataset.kind=kind;}
  async function update(){
    try{status=(await api('connections')).providers;draw();}
    catch(e){$('connectionCards').replaceChildren(el('p','connection-result',e.message));}
  }
  function draw(){
    const root=$('connectionCards');root.replaceChildren();
    for(const [id,name,description,url] of providers){
      const card=el('section','connection-card');
      const head=el('div','connection-card-head'),title=el('div');title.append(el('h3','',name),el('p','',description));
      const info=status[id]||{};const badge=el('span','connection-badge',id==='ollama'?'Local':info.configured?'Clé enregistrée':info.source==='locked'?'Trousseau verrouillé':'Non connecté');
      if(info.configured)badge.classList.add('connected');head.append(title,badge);card.append(head);
      const link=el('a','text-link',id==='ollama'?'Installer Ollama ↗':'Obtenir une clé ↗');link.href=url;link.target='_blank';link.rel='noopener noreferrer';card.append(link);
      if(id==='github')card.append(el('p','connection-help','Jeton à accès limité : dépôts choisis, Contents et Pull requests selon les besoins.'));
      const result=el('p','connection-result');result.setAttribute('role','status');
      const actions=el('div','connection-actions');
      if(id!=='ollama'){
        const label=el('label','connection-label',info.configured?'Remplacer la clé':'Coller la clé API');label.htmlFor='connection-key-'+id;
        const input=el('input','field');input.id=label.htmlFor;input.type='password';input.autocomplete='off';input.spellcheck=false;input.placeholder='••••••••••••';input.maxLength=4096;
        if(info.source==='environment'){input.disabled=true;label.textContent='Clé fournie par le système';}
        card.append(label,input);
        const save=el('button','primary','Enregistrer');save.disabled=info.source==='environment';
        save.onclick=async()=>{if(!input.value.trim())return setResult(result,'Collez votre clé.','error');save.disabled=true;try{await api('connections/save',{provider:id,secret:input.value});input.value='';await update();await refresh();}catch(e){setResult(result,e.message,'error')}finally{input.value='';save.disabled=false}};
        actions.append(save);
        if(info.configured&&info.source==='keychain'){
          const remove=el('button','ghost','Retirer');remove.onclick=async()=>{if(!confirm('Retirer la clé de '+name+' du trousseau local ?'))return;remove.disabled=true;try{await api('connections/remove',{provider:id});await update();await refresh()}catch(e){setResult(result,e.message,'error')}finally{remove.disabled=false}};actions.append(remove);
        }
      }
      const test=el('button','ghost',id==='ollama'?'Détecter Ollama':'Tester');test.onclick=async()=>{test.disabled=true;setResult(result,'Vérification…');try{const data=await api('connections/test',{provider:id});setResult(result,'Connexion réussie'+(id==='ollama'?(data.models.length?' · '+data.models.join(', '):' · aucun modèle installé'):'')+'.','success');if(id==='ollama')badge.textContent='Détecté';}catch(e){setResult(result,e.message,'error')}finally{test.disabled=false}};actions.append(test);
      card.append(actions,result);root.append(card);
      if(id==='ollama'&&detectOnOpen){detectOnOpen=false;test.click();}
    }
  }
  function open(){if(dialog.open)return;detectOnOpen=true;dialog.showModal();$('connectionCards').replaceChildren(el('p','connection-result','Chargement…'));update();}
  function close(){dialog.querySelectorAll('input[type=password]').forEach(i=>i.value='');try{localStorage.setItem('suxenai-onboarding-v8','1')}catch{}dialog.close();}
  $('openConnections').onclick=open;$('closeConnections').onclick=close;$('skipConnections').onclick=close;$('finishConnections').onclick=close;
  dialog.addEventListener('cancel',e=>{e.preventDefault();close()});
  // In v1.0 the three modes are visible immediately; connecting APIs is optional.
})();

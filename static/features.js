(() => {
  const dialog=$('toolsDialog'), root=$('toolsContent');let selected='project', generation=0;
  const btn=(label,fn,cls='ghost')=>{const b=el('button',cls,label);b.onclick=async()=>{b.disabled=true;try{await fn()}catch(e){toast(e.message)}finally{b.disabled=false}};return b;};
  const input=(placeholder,type='text')=>{const i=el('input','field');i.type=type;i.placeholder=placeholder;i.setAttribute('aria-label',placeholder);return i;};
  const block=(heading,description)=>{const c=el('section','v9-card');c.append(el('h3','',heading),el('p','inspector-info',description));root.append(c);return c;};
  const download=(data,name)=>{const url=URL.createObjectURL(new Blob([JSON.stringify(data,null,2)],{type:'application/json'}));const a=el('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};
  async function draw(tab){
    const seq=++generation,pid=projectId;selected=tab;root.replaceChildren();document.querySelectorAll('[data-v9tab]').forEach(b=>b.classList.toggle('active',b.dataset.v9tab===tab));
    $('toolsProject').textContent=activeProject()?.name||'Aucun projet';
    if(tab==='project'){
      const p=activeProject();if(!p)return block('Aucun projet','Créez un projet depuis la barre latérale.');
      const c=block('Projet','Nom, dépôt GitHub facultatif et consignes communes transmises à toutes les IA.');
      const name=input('Nom du projet');name.value=p.name;const repo=input('URL GitHub (facultative)');repo.value=p.repo||'';
      const instr=el('textarea','field');instr.rows=5;instr.placeholder='Consignes communes';instr.setAttribute('aria-label','Consignes communes');instr.value=p.instructions||'';
      c.append(el('label','field-label','Nom'),name,el('label','field-label','Dépôt GitHub'),repo,el('label','field-label','Consignes communes'),instr);
      root.append(btn('Enregistrer',async()=>{await api('projects/update',{id:pid,name:name.value,repo:repo.value,instructions:instr.value});toast('Projet enregistré');await refresh()},'primary'));
    }else if(tab==='connections'){
      const c=block('Connexions IA','Nécessaires uniquement pour le mode API. Créez une clé chez le fournisseur, collez-la, puis testez. Les clés restent dans le trousseau du système. Les abonnements web ne sont pas des clés API.');
      const cards=el('div','connection-cards');c.append(cards);window.suxenConnections.mount(cards);
    }else if(tab==='prefs'){
      if(!pid)return block('Sélectionnez un projet','Les réglages sont propres à chaque projet.');
      const p=await api('v9/preferences?project='+encodeURIComponent(pid));if(seq!==generation)return;
      const m=block('Mémoire intelligente','Retrouve jusqu’à cinq extraits pertinents des autres discussions de ce projet. Ils sont transmis aux IA lors des nouvelles réponses si ce réglage est activé.');
      const recall=el('input');recall.type='checkbox';recall.checked=!!p.recall;const r=el('label','v9-toggle');r.append(recall,document.createTextNode('Activer la recherche de mémoire'));m.append(r);
      root.append(btn('Enregistrer les réglages',async()=>{await api('v9/preferences',{project:pid,local_only:!!p.local_only,recall:recall.checked});toast('Réglages enregistrés');await refresh()},'primary'));
    }else if(tab==='models'){
      const c=block('Ollama — modèles installés','Démarrez Ollama sur votre Mac. Les téléchargements peuvent nécessiter plusieurs Go.');const list=el('div','v9-list');c.append(list);
      const refreshModels=async()=>{const {models}=await api('v9/models');list.replaceChildren();if(!models.length)list.append(el('p','inspector-info','Aucun modèle installé'));for(const model of models){const row=el('div','v9-row');row.append(el('span','',model),btn('Ajouter à la discussion',async()=>{const cid=chatId;if(!cid)throw Error('Créez une discussion d’abord');await api('agents',{chat:cid,name:model.slice(0,50),provider:'ollama',model});await refresh();toast('IA locale ajoutée')}));list.append(row)}};
      c.append(btn('Actualiser',refreshModels));const name=input('Nom du modèle, ex. llama3.2');c.append(name,btn('Télécharger',async()=>{if(!name.value.trim()||!confirm('Télécharger '+name.value+' via Ollama ? Le fichier peut être volumineux.'))return;await api('v9/pull',{name:name.value.trim(),confirm:'DOWNLOAD_MODEL'});await refreshModels();toast('Modèle installé')},'primary'));
      try{await refreshModels()}catch(e){list.append(el('p','inspector-info','Ollama non détecté. Installez-le puis démarrez-le.'));const a=el('a','text-link','Télécharger Ollama ↗');a.href='https://ollama.com/';a.target='_blank';a.rel='noopener noreferrer';list.append(a)}
    }else if(tab==='costs'){
      if(!pid)return block('Sélectionnez un projet','La consommation est enregistrée par projet.');
      const data=await api('v9/usage?project='+encodeURIComponent(pid));if(seq!==generation)return;
      const c=block('Consommation mesurée','Tokens rapportés par les fournisseurs depuis la v0.9. Coût indicatif en USD avec les tarifs saisis par modèle ; ce n’est pas une facture.');
      if(!data.usage.length)c.append(el('p','inspector-info','Aucune consommation enregistrée.'));
      for(const u of data.usage){const row=el('div','v9-row');row.append(el('strong','',u.provider+' · '+u.model),el('span','',u.calls+' appels · '+(u.input_tokens??'—')+' / '+(u.output_tokens??'—')+' tokens · '+(u.estimated_usd===null?'Tarif inconnu':'$'+u.estimated_usd.toFixed(4))+(u.unpriced?' ('+u.unpriced+' non tarifés)':'')));c.append(row)}
      const rates=block('Tarifs personnalisés','Saisissez les tarifs officiels en USD pour un million de tokens. Les nouveaux appels utilisent ces tarifs.');const provider=el('select','field');for(const p of ['openai','anthropic','mistral','gemini'])provider.add(new Option(p,p));const model=input('Identifiant exact du modèle'),it=input('USD par million de tokens en entrée','number'),ot=input('USD par million de tokens en sortie','number');it.min=ot.min='0';it.step=ot.step='any';rates.append(provider,model,it,ot,btn('Enregistrer le tarif',async()=>{if(it.value===''||ot.value==='')throw Error('Saisissez les deux tarifs');await api('v9/rate',{provider:provider.value,model:model.value,input_rate:Number(it.value),output_rate:Number(ot.value)});toast('Tarif enregistré');draw('costs')},'primary'));
    }else if(tab==='backup'){
      const c=block('Sauvegarde complète','Projets, discussions, équipes, documents, historique d’atelier et consommation. Les clés API du trousseau sont exclues. Le fichier contient vos textes privés : conservez-le en lieu sûr.');
      c.append(btn('Télécharger une sauvegarde',async()=>download(await api('v9/backup'),'suxenai-backup.json'),'primary'),btn('Restaurer une copie',()=>{$('backupFile').value='';$('backupFile').click()}));
    }else if(tab==='updates'){
      const c=block('SuxenAI 1.2.0','Logiciel libre (MIT), local et privé. Les nouvelles versions publiées sur GitHub restent des téléchargements manuels.');
      const automatic=el('input');automatic.type='checkbox';automatic.checked=localStorage.getItem('suxenai-auto-updates')==='1';const label=el('label','v9-toggle');label.append(automatic,document.createTextNode('Vérifier automatiquement les versions au démarrage'));automatic.onchange=()=>localStorage.setItem('suxenai-auto-updates',automatic.checked?'1':'0');c.append(label);
      c.append(btn('Vérifier les mises à jour',async()=>{const x=await api('v9/update');c.append(el('p','connection-result',x.available?'Version '+x.latest+' disponible':x.message||'Vous êtes à jour'));const a=el('a','text-link','Ouvrir les versions GitHub ↗');a.href=x.url;a.target='_blank';a.rel='noopener noreferrer';c.append(a)}));
    }
  }
  function open(tab='project'){if(!dialog.open)dialog.showModal();draw(tab).catch(e=>toast(e.message));}
  $('settings').onclick=()=>open();$('backupTools').onclick=()=>open('backup');window.openSettings=open;$('closeTools').onclick=()=>dialog.close();document.querySelectorAll('[data-v9tab]').forEach(b=>b.onclick=()=>draw(b.dataset.v9tab).catch(e=>toast(e.message)));
  $('backupFile').onchange=async()=>{const f=$('backupFile').files[0];if(!f)return;try{if(f.size>10000000)throw Error('Sauvegarde limitée à 10 Mo');if(!confirm('Restaurer les projets sous forme de copies ? Les données existantes seront conservées.'))return;const backup=JSON.parse(await f.text());const r=await api('v9/restore',{backup,confirm:'RESTORE_COPY'});await refresh();toast(r.projects+' projets restaurés')}catch(e){toast(e.message)}};
  $('focusMode').onclick=()=>{document.body.classList.toggle('focus-mode');$('focusMode').setAttribute('aria-pressed',String(document.body.classList.contains('focus-mode')))};
  const renderOld=render;render=function(){renderOld();const pid=projectId,cid=chatId;if(!pid)return;api('v9/preferences?project='+encodeURIComponent(pid)).then(p=>{if(pid!==projectId||cid!==chatId)return;const nodes=$('agents').querySelectorAll('.agent');members().forEach((a,i)=>{const available=state.providers.find(x=>x.id===a.provider)?.available;const blocked=p.mode==='web'||(p.local_only&&!['ollama','demo'].includes(a.provider))||!available;if(blocked&&nodes[i]){nodes[i].classList.add('agent-unavailable');nodes[i].title=p.mode==='web'?'En pause en mode Web':!available?'Clé API manquante (Réglages → Connexions IA)':'Hors mode local';const why=p.mode==='web'?'':!available?'clé requise':'hors local';if(why&&!nodes[i].querySelector('.why'))nodes[i].querySelector('.agent-info').append(el('span','why',why))}})}).catch(()=>{})};
  try{if(localStorage.getItem('suxenai-auto-updates')==='1')api('v9/update').then(x=>{if(x.available)toast('SuxenAI '+x.latest+' disponible dans Réglages → À propos')}).catch(()=>{})}catch{}
})();

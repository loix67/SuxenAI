(() => {
  const bridge=window.suxenDesktop;if(!bridge)return;
  window.suxenSelectedSlot=0;
  const root=el('section','desktop-controls'),header=el('div','desktop-controls-head');header.append(el('strong','','Affichage dans la fenêtre'));root.append(header);
  const selector=el('div','desktop-slot-selector'),states=el('div','desktop-browser-state');root.append(selector,states,el('p','desktop-note','Choisissez un panneau, puis une IA ci-dessous. Si un site refuse la connexion intégrée, utilisez « Navigateur externe ».'));
  $('webProviders').before(root);$('webTitle').textContent='Vos IA, dans SuxenAI.';
  const explain=$('webTitle').parentElement.querySelector('p:not(.eyebrow)');if(explain)explain.textContent='Ouvrez les sites officiels à côté de la discussion, puis rapportez les réponses ici.';
  let current=[null,null];
  function button(label,fn){const b=el('button','ghost',label);b.onclick=async()=>{try{await fn()}catch(e){toast(e.message)}};return b;}
  function draw(state){current=state;selector.replaceChildren();states.replaceChildren();for(let i=0;i<2;i++){const b=button(i===0?'Panneau 1':'Panneau 2',()=>{window.suxenSelectedSlot=i;draw(current)});if(window.suxenSelectedSlot===i)b.classList.add('active');selector.append(b);const item=state[i];if(!item)continue;const row=el('div','desktop-browser-row'),meta=el('div','desktop-browser-meta');meta.append(el('strong','',item.name),el('small','',item.domain));row.append(meta);const actions=el('div','desktop-browser-actions');actions.append(button('← Retour',()=>bridge.back(i)),button('↻ Recharger',()=>bridge.reload(i)),button('Navigateur externe ↗',()=>bridge.external(item.id)),button('Fermer',()=>bridge.close(i)));row.append(actions);if(item.error)row.append(el('p','desktop-browser-error',item.error));states.append(row);}}
  bridge.state().then(draw).catch(e=>toast(e.message));bridge.onState(draw);
  const observer=new MutationObserver(()=>{if(document.body.dataset.execution!=='web'&&current.some(Boolean)){Promise.resolve(bridge.close(1)).then(()=>bridge.close(0)).catch(()=>{});}});observer.observe(document.body,{attributes:true,attributeFilter:['data-execution']});
})();

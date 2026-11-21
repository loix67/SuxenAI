"""Local workspace enhancements: policy, usage, recall and managed local models."""
import json
import math
import re
import urllib.error
import urllib.request
import connections

VERSION='1.1.0'
LOCAL_PROVIDERS={'ollama','demo'}


def policy(db,pid):
    p=db.one('SELECT * FROM project_preferences WHERE project=?',(pid,)) or {'project':pid,'local_only':0,'recall':0}
    web=db.one('SELECT enabled FROM project_web_modes WHERE project=?',(pid,))
    p['mode']='web' if web and web['enabled'] else 'local' if p['local_only'] else 'api'
    return p


def set_policy(db,pid,local_only,recall):
    if not db.one('SELECT id FROM projects WHERE id=?',(pid,)):raise ValueError('Projet introuvable')
    with db.LOCK,db.connection() as con:
        con.execute('INSERT OR REPLACE INTO project_preferences VALUES(?,?,?)',(pid,int(local_only is True),int(recall is True)))
        if local_only is True:con.execute('INSERT OR REPLACE INTO project_web_modes VALUES(?,0)',(pid,))


def set_mode(db,pid,mode):
    if mode not in ('web','api','local'):raise ValueError('Mode inconnu')
    if not db.one('SELECT id FROM projects WHERE id=?',(pid,)):raise ValueError('Projet introuvable')
    with db.LOCK,db.connection() as con:
        previous=con.execute('SELECT recall FROM project_preferences WHERE project=?',(pid,)).fetchone()
        con.execute('INSERT OR REPLACE INTO project_preferences VALUES(?,?,?)',(pid,int(mode=='local'),previous['recall'] if previous else 0))
        con.execute('INSERT OR REPLACE INTO project_web_modes VALUES(?,?)',(pid,int(mode=='web')))


def provider_allowed(db,pid,provider):
    p=policy(db,pid)
    if p['mode']=='web':return False
    if p['local_only'] and provider not in LOCAL_PROVIDERS:return False
    if provider in LOCAL_PROVIDERS:return True
    return provider in connections.ENV and provider!='github' and connections.status(provider)['configured']


def usage_tokens(provider,response):
    usage=response.get('usage') or {}
    if provider=='anthropic':keys=('input_tokens','output_tokens')
    elif provider=='gemini':usage=response.get('usageMetadata') or {};keys=('promptTokenCount','candidatesTokenCount')
    else:keys=('prompt_tokens','completion_tokens')
    def valid(v):return v if type(v) is int and 0<=v<=10**9 else None
    return valid(usage.get(keys[0])),valid(usage.get(keys[1]))


def record_usage(db,pid,provider,model,response):
    it,ot=usage_tokens(provider,response)
    if provider in LOCAL_PROVIDERS:cost=0.0
    else:
        rate=db.one('SELECT input_rate,output_rate FROM model_rates WHERE provider=? AND model=?',(provider,model))
        cost=(it*rate['input_rate']+ot*rate['output_rate'])/1_000_000 if rate and it is not None and ot is not None else None
    db.write('INSERT INTO api_usage VALUES(?,?,?,?,?,?,?,?)',(db.uid(),pid,provider,model,it,ot,cost,db.now()))


def save_rate(db,provider,model,input_rate,output_rate):
    if provider not in ('openai','anthropic','mistral','gemini') or not isinstance(model,str) or not model.strip() or len(model)>100:raise ValueError('Modèle invalide')
    rates=[float(input_rate),float(output_rate)]
    if any(not math.isfinite(x) or x<0 or x>100000 for x in rates):raise ValueError('Tarif invalide')
    db.write('INSERT OR REPLACE INTO model_rates VALUES(?,?,?,?)',(provider,model,*rates))


def usage_report(db,pid):
    return db.query('SELECT provider,model,count(*) AS calls,sum(input_tokens) AS input_tokens,sum(output_tokens) AS output_tokens,sum(estimated_usd) AS estimated_usd,sum(CASE WHEN estimated_usd IS NULL THEN 1 ELSE 0 END) AS unpriced FROM api_usage WHERE project=? GROUP BY provider,model ORDER BY provider,model',(pid,))


def recall(db,pid,cid,question):
    """Opt-in lexical recall, scoped to the project; no embeddings or external calls."""
    terms=set(re.findall(r'\w{4,}',question.lower()))
    if not terms:return []
    rows=db.query('SELECT m.content,m.speaker,c.title FROM messages m JOIN chats c ON c.id=m.chat WHERE c.project=? AND c.id!=? ORDER BY m.rowid DESC LIMIT 1000',(pid,cid))
    scored=[]
    for row in rows:
        content=row['content'][:4000];overlap=terms & set(re.findall(r'\w{4,}',content.lower()))
        if overlap:scored.append((len(overlap),row['title'],row['speaker'],content[:1200]))
    scored.sort(key=lambda x:x[0],reverse=True)
    return [{'title':title,'speaker':speaker,'text':text} for _,title,speaker,text in scored[:5]]


def local_models():
    return connections.test('ollama')['models']


def pull_model(name):
    if not isinstance(name,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.:-]{0,100}',name):raise ValueError('Nom de modèle Ollama invalide')
    payload=json.dumps({'model':name,'stream':False}).encode()
    request=urllib.request.Request('http://127.0.0.1:11434/api/pull',data=payload,headers={'Content-Type':'application/json'},method='POST')
    try:
        with connections.opener().open(request,timeout=900) as response:
            result=json.loads(response.read(1000000))
        if result.get('status')!='success':raise ValueError('Téléchargement non terminé')
        return {'ok':True}
    except (OSError,ValueError):raise ValueError('Ollama indisponible ou téléchargement incomplet. Vérifiez le modèle et l’espace disque.') from None


def update_check():
    # Only an advisory check, never download or execute unsigned code.
    from repository import github_get
    try:release=github_get('/repos/loix67/SuxenAI/releases/latest')
    except ValueError:return {'version':VERSION,'available':False,'message':'Aucune version publiée accessible. Consultez GitHub.','url':'https://github.com/loix67/SuxenAI/releases'}
    tag=str(release.get('tag_name','')).lstrip('v')
    def numeric(s):
        if not re.fullmatch(r'\d+(\.\d+){1,2}',s):return ()
        parts=tuple(int(x) for x in s.split('.'));return parts+(0,)*(3-len(parts))
    return {'version':VERSION,'latest':tag,'available':bool(numeric(tag) and numeric(tag)>numeric(VERSION)),'url':'https://github.com/loix67/SuxenAI/releases'}

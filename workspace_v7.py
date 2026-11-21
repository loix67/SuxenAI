"""Local, explicitly shared project documents and durable memory."""
import difflib
import ast
import json
from repository import validate_path


def save_item(db, project, kind, name, content, shared=False):
    if not db.one('SELECT id FROM projects WHERE id=?', (project,)):
        raise ValueError('Projet introuvable')
    if kind not in ('document', 'memory'):
        raise ValueError('Type inconnu')
    name = validate_path(name.strip())
    if not isinstance(content, str) or not content.strip() or '\x00' in content or len(content.encode()) > 80000:
        raise ValueError('Texte UTF-8 requis, maximum 80 Ko')
    ident = db.uid()
    with db.LOCK, db.connection() as con:
        if con.execute('SELECT count(*) FROM workspace_items WHERE project=?', (project,)).fetchone()[0] >= 100:
            raise ValueError('Maximum 100 éléments par projet')
        con.execute('INSERT INTO workspace_items VALUES(?,?,?,?,?,?,?)',
                    (ident, project, kind, name, content, int(shared is True), db.now()))
    return ident


def context(db, project):
    items = db.query('SELECT kind,name,content FROM workspace_items WHERE project=? AND shared=1 ORDER BY rowid', (project,))
    return '\n\n'.join(f'{x["kind"]}: {x["name"]}\n{x["content"]}' for x in items)[:60000]


def diff(original, content, path):
    return ''.join(difflib.unified_diff(original.splitlines(True), content.splitlines(True),
                                         fromfile='a/'+path, tofile='b/'+path))


def static_checks(path, content):
    """Parse only; never import, execute or invoke commands from proposals."""
    try:
        if path.endswith('.py'):
            ast.parse(content, filename=path)
        elif path.endswith('.json'):
            json.loads(content)
        else:
            return {'status': 'skipped', 'message': 'Aucun analyseur statique pour ce type'}
    except (SyntaxError, ValueError, RecursionError) as exc:
        return {'status': 'failed', 'message': str(exc)}
    return {'status': 'passed', 'message': 'Syntaxe valide (aucune exécution)'}


def export_project(db, pid):
    p = db.one('SELECT name,repo,instructions FROM projects WHERE id=?', (pid,))
    if not p:
        raise ValueError('Projet introuvable')
    chats = db.query('SELECT id,title FROM chats WHERE project=?', (pid,))
    return {'format':'suxenai-project-v1','project':p,
            'chats':[{'title':c['title'],'messages':db.history(c['id'])} for c in chats],
            'items':db.query('SELECT kind,name,content FROM workspace_items WHERE project=?',(pid,))}


def import_project(db, payload):
    if not isinstance(payload,dict) or payload.get('format')!='suxenai-project-v1':
        raise ValueError('Export de projet SuxenAI attendu')
    p, chats, items = payload['project'], payload.get('chats',[]), payload.get('items',[])
    if not isinstance(chats,list) or not isinstance(items,list) or len(chats)>100 or len(items)>100:
        raise ValueError('Maximum 100 discussions et éléments')
    pid=db.uid()
    with db.LOCK, db.connection() as con:
        con.execute('INSERT INTO projects VALUES(?,?,?,?,?)',(pid,str(p['name'])[:120],'',str(p.get('instructions',''))[:4000],db.now()))
        for c in chats:
            cid=db.uid(); messages=c.get('messages',[])
            if not isinstance(messages,list) or len(messages)>500:raise ValueError('Maximum 500 messages par discussion')
            con.execute('INSERT INTO chats VALUES(?,?,?,?,?,?,?)',(cid,pid,str(c['title'])[:120],None,'free','',db.now()))
            for m in messages:
                con.execute('INSERT INTO messages VALUES(?,?,?,?,?)',(db.uid(),cid,str(m['speaker'])[:60],str(m['content'])[:20000],db.now()))
        for item in items:
            name=validate_path(item['name']); content=item['content']; kind=item['kind']
            if kind not in ('document','memory') or not isinstance(content,str) or '\x00' in content or not content.strip() or len(content.encode())>80000:
                raise ValueError('Document invalide')
            con.execute('INSERT INTO workspace_items VALUES(?,?,?,?,?,?,?)',(db.uid(),pid,kind,name,content,0,db.now()))
    return pid

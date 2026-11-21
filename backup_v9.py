"""Versioned, credential-free workspace snapshot. Restore adds copies atomically."""
import json
import re

TABLES=('projects','chats','agents','messages','project_files','import_origins','workspace_items','change_batches','proposals','project_preferences','api_usage','model_rates','project_web_modes')


def export_backup(db):
    with db.LOCK,db.connection() as con:
        con.execute('BEGIN')
        return {'format':'suxenai-backup-v1','tables':{table:[dict(r) for r in con.execute('SELECT * FROM '+table)] for table in TABLES}}


def restore_backup(db,payload):
    if not isinstance(payload,dict) or payload.get('format')!='suxenai-backup-v1' or not isinstance(payload.get('tables'),dict):raise ValueError('Sauvegarde SuxenAI invalide')
    tables=dict(payload['tables']);tables.setdefault('project_web_modes',[])
    if set(tables)!=set(TABLES):raise ValueError('Sauvegarde incomplète')
    if any(not isinstance(rows,list) for rows in tables.values()) or sum(len(rows) for rows in tables.values())>50000:raise ValueError('Sauvegarde trop volumineuse')
    ids={}
    for table in ('projects','chats','agents','messages','workspace_items','change_batches','proposals','api_usage'):
        ids[table]={}
        for row in tables[table]:
            if not isinstance(row,dict) or not isinstance(row.get('id'),str) or row['id'] in ids[table]:raise ValueError('Identifiants invalides')
            ids[table][row['id']]=db.uid()
    def ref(table,value,optional=False):
        if optional and not value:return value
        if value not in ids[table]:raise ValueError('Référence manquante dans la sauvegarde')
        return ids[table][value]
    with db.LOCK,db.connection() as con:
        for table in TABLES:
            columns=[r['name'] for r in con.execute('PRAGMA table_info('+table+')')]
            for original in tables[table]:
                if not isinstance(original,dict) or set(original)!=set(columns) or any(not isinstance(x,(str,int,float,type(None))) for x in original.values()):raise ValueError('Structure de sauvegarde invalide')
                row=dict(original)
                if table in ids:row['id']=ref(table,row['id'])
                if 'project' in row:row['project']=ref('projects',row['project'])
                if 'chat' in row:row['chat']=ref('chats',row['chat'])
                if table=='projects':row['name']=str(row['name'])[:100]+' · restauré';row['repo']=''
                if table=='chats':row['parent']=ref('chats',row['parent'],True);row['coordinator']=ref('agents',row['coordinator'],True) if row['coordinator'] in ids['agents'] else ''
                if table=='workspace_items':row['shared']=0
                if table=='project_preferences':row['recall']=0;row['local_only']=1
                if table=='project_web_modes':row['enabled']=0
                if table in ('change_batches','proposals'):
                    row['author']=ref('agents',row['author']);row['reviewer']=ref('agents',row['reviewer'],True) if row['reviewer'] in ids['agents'] else ''
                    row['status']='archived'
                    if not isinstance(row['pr_url'],str) or not re.fullmatch(r'https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/pull/\d+',row['pr_url']):row['pr_url']=''
                    if table=='change_batches':
                        if not isinstance(json.loads(row['files']),list):raise ValueError('Lot sauvegardé invalide')
                if table=='model_rates':
                    con.execute('INSERT OR IGNORE INTO model_rates VALUES(?,?,?,?)',tuple(row[c] for c in columns));continue
                con.execute('INSERT INTO '+table+' ('+','.join(columns)+') VALUES ('+','.join('?' for _ in columns)+')',tuple(row[c] for c in columns))
        # Restored projects start in local-only mode and recall disabled, even for old snapshots.
        for pid in ids['projects'].values():con.execute('INSERT OR IGNORE INTO project_preferences VALUES(?,1,0)',(pid,))
    return {'projects':len(ids['projects'])}

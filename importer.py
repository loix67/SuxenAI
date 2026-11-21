"""SuxenAI v0.6 portable conversation import.

Strictly local parsing. Exports are never forwarded to model providers during
preview. Only the conversations explicitly selected by the user are stored.
"""
import base64
import io
import json
import re
import zipfile

MAX_UPLOAD_BYTES=8_000_000
MAX_EXTRACTED_BYTES=24_000_000
MAX_PREVIEW_CONVERSATIONS=400
MAX_IMPORT_CONVERSATIONS=100
MAX_MESSAGES_PER_CONVERSATION=500
MAX_TEXT_CHARS=12000


def _read_export(encoded, filename):
    if not isinstance(encoded,str) or len(encoded)>MAX_UPLOAD_BYTES*1.4:
        raise ValueError("Export trop volumineux (8 Mo maximum)")
    try: raw=base64.b64decode(encoded,validate=True)
    except Exception: raise ValueError("Encodage du fichier invalide")
    if len(raw)>MAX_UPLOAD_BYTES:raise ValueError("Export trop volumineux (8 Mo maximum)")
    if filename.lower().endswith(".zip"):
        try:
            with zipfile.ZipFile(io.BytesIO(raw)) as archive:
                names=[x for x in archive.infolist() if not x.is_dir() and
                       x.filename.split("/")[-1].lower() in ("conversations.json","claude_conversations.json")]
                if not names:
                    raise ValueError("Aucun fichier conversations.json compatible dans le ZIP")
                names.sort(key=lambda x: (x.filename.split("/")[-1].lower()!="conversations.json",len(x.filename)))
                item=names[0]
                if item.file_size>MAX_EXTRACTED_BYTES:raise ValueError("JSON décompressé trop volumineux")
                with archive.open(item) as stream:raw=stream.read(MAX_EXTRACTED_BYTES+1)
                if len(raw)>MAX_EXTRACTED_BYTES:raise ValueError("JSON décompressé trop volumineux")
        except (zipfile.BadZipFile,RuntimeError) as e:raise ValueError("Archive ZIP illisible")
    elif not filename.lower().endswith(".json"):
        raise ValueError("Fichier JSON ou ZIP attendu")
    try:return json.loads(raw.decode("utf-8-sig"))
    except (ValueError,UnicodeDecodeError):raise ValueError("Fichier JSON non valide")


def _text(content):
    if isinstance(content,str):return content[:MAX_TEXT_CHARS]
    if isinstance(content,list):
        return "\n".join(_text(x) for x in content)[:MAX_TEXT_CHARS]
    if not isinstance(content,dict):return ""
    if isinstance(content.get("parts"),list):return _text(content["parts"])
    if isinstance(content.get("text"),str):return content["text"][:MAX_TEXT_CHARS]
    if isinstance(content.get("content"),(str,list)):return _text(content["content"])
    if content.get("type")=="text" and isinstance(content.get("value"),str):
        return content["value"][:MAX_TEXT_CHARS]
    return ""


def _chatgpt(conv,index):
    mapping=conv.get("mapping",{})
    if not isinstance(mapping,dict):return None
    end=conv.get("current_node")
    chain=[]
    seen=set()
    if end in mapping:
        while end in mapping and end not in seen:
            seen.add(end);node=mapping[end];chain.append(node)
            end=node.get("parent") if isinstance(node,dict) else None
        chain.reverse()
    else:
        # Older exports may omit current_node: retain a deterministic timeline.
        chain=sorted((n for n in mapping.values() if isinstance(n,dict)),
                     key=lambda n: ((n.get("message") or {}).get("create_time") or 0))
    messages=[]
    for node in chain:
        message=node.get("message")
        if not isinstance(message,dict):continue
        author=message.get("author") or {}
        role=author.get("role","unknown") if isinstance(author,dict) else "unknown"
        if role not in ("user","assistant","system"):continue
        content=_text(message.get("content"))
        if content.strip():messages.append({"speaker":"Vous" if role=="user" else "ChatGPT · "+role,
                                           "content":content,"source_role":role})
    return {"id":str(index),"source":"ChatGPT","title":str(conv.get("title") or "Conversation ChatGPT")[:160],
            "messages":messages[:MAX_MESSAGES_PER_CONVERSATION]}


def _claude(conv,index):
    raw=conv.get("chat_messages",conv.get("messages"))
    if not isinstance(raw,list):return None
    messages=[]
    for item in raw:
        if not isinstance(item,dict):continue
        sender=str(item.get("sender",item.get("role","assistant"))).lower()
        role="user" if sender in ("human","user") else "assistant"
        content=_text(item.get("content") or item.get("text") or item.get("message"))
        if content.strip():messages.append({"speaker":"Vous" if role=="user" else "Claude · assistant",
                                           "content":content,"source_role":role})
    return {"id":str(index),"source":"Claude","title":str(conv.get("name") or conv.get("title") or "Conversation Claude")[:160],
            "messages":messages[:MAX_MESSAGES_PER_CONVERSATION]}


def parse_export(encoded,filename,source="auto"):
    raw=_read_export(encoded,filename)
    if isinstance(raw,dict):
        raw=raw.get("conversations",raw.get("chats",raw))
    if not isinstance(raw,list):raise ValueError("Format inconnu : une liste de conversations est attendue")
    if len(raw)>MAX_PREVIEW_CONVERSATIONS:raise ValueError("Export limité à 400 conversations par import")
    result=[]
    for index,conv in enumerate(raw):
        if not isinstance(conv,dict):continue
        detected="chatgpt" if isinstance(conv.get("mapping"),dict) else (
                 "claude" if isinstance(conv.get("chat_messages"),list) or isinstance(conv.get("messages"),list) else "")
        if source in ("chatgpt","claude") and detected and source!=detected:continue
        item=_chatgpt(conv,index) if detected=="chatgpt" else (_claude(conv,index) if detected=="claude" else None)
        if item and item["messages"]:result.append(item)
    if not result:raise ValueError("Aucune conversation ChatGPT ou Claude compatible trouvée")
    return result


def preview(encoded,filename,source="auto"):
    records=parse_export(encoded,filename,source)
    return {"conversations":[{"id":x["id"],"source":x["source"],"title":x["title"],
             "messages":len(x["messages"]),"first_message":x["messages"][0]["content"][:180]} for x in records],
            "count":len(records)}


def import_selected(db, project_id, encoded, filename, selected_ids, source="auto", template_chat=None):
    if not isinstance(selected_ids,list) or not selected_ids or len(selected_ids)>MAX_IMPORT_CONVERSATIONS:
        raise ValueError("Sélectionner entre 1 et 100 conversations")
    wanted={str(x) for x in selected_ids}
    if len(wanted)!=len(selected_ids):raise ValueError("Sélection contenant des doublons")
    project=db.one("SELECT id FROM projects WHERE id=?",(project_id,))
    if not project:raise ValueError("Projet introuvable")
    conversations=parse_export(encoded,filename,source)
    template_agents=[]
    if template_chat:
        existing=db.one("SELECT id FROM chats WHERE id=? AND project=?",(template_chat,project_id))
        if not existing:raise ValueError("Discussion source invalide")
        template_agents=db.agents(template_chat)
    chosen=[x for x in conversations if x["id"] in wanted]
    if len(chosen)!=len(wanted):raise ValueError("Certaines conversations sélectionnées sont absentes")
    imported=[]
    # One transaction per import: no partial database state if anything fails.
    with db.LOCK,db.connection() as con:
        for item in chosen:
            cid=db.uid()
            con.execute("INSERT INTO chats VALUES(?,?,?,?,?,?,?)",
                (cid,project_id,"["+item["source"]+"] "+item["title"][:105],
                 None,"free","",db.now()))
            for m in item["messages"]:
                con.execute("INSERT INTO messages VALUES(?,?,?,?,?)",
                    (db.uid(),cid,m["speaker"],m["content"],db.now()))
            for agent in template_agents:
                con.execute("INSERT INTO agents VALUES(?,?,?,?,?,?,?)",(
                    db.uid(),cid,agent["name"],agent["provider"],agent["model"],
                    agent["role"],agent["enabled"]))
            con.execute("INSERT INTO import_origins VALUES(?,?,?,?,?)",
                (cid,item["source"],filename,item["id"],db.now()))
            imported.append({"id":cid,"source":item["source"],"title":item["title"],
                             "messages":len(item["messages"])})
    return {"imported":imported,"count":len(imported)}

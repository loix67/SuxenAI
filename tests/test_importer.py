import base64
import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

import importer
import server


def payload(data):
    return base64.b64encode(json.dumps(data,ensure_ascii=False).encode()).decode()


class ConversationImportTests(unittest.TestCase):
    def test_chatgpt_main_branch_and_roles(self):
        data=[{"title":"Projet architecture","current_node":"n3","mapping":{
            "n1":{"parent":None,"message":{"author":{"role":"user"},"content":{"parts":["Bonjour"]}}},
            "n2":{"parent":"n1","message":{"author":{"role":"assistant"},"content":{"parts":["Voici une réponse"]}}},
            "n3":{"parent":"n2","message":{"author":{"role":"user"},"content":{"parts":["Peux-tu continuer ?"]}}},
            "sibling":{"parent":"n1","message":{"author":{"role":"assistant"},"content":{"parts":["Réponse de branche abandonnée"]}}}
        }}]
        records=importer.parse_export(payload(data),"conversations.json")
        self.assertEqual(len(records),1)
        self.assertEqual([x["source_role"] for x in records[0]["messages"]],["user","assistant","user"])
        self.assertEqual(len(records[0]["messages"]),3)
        self.assertNotIn("abandonnée",str(records))

    def test_claude_content_blocks(self):
        data=[{"name":"Audit code","chat_messages":[
            {"sender":"human","content":[{"type":"text","text":"Vérifie ce code"}]},
            {"sender":"assistant","content":[{"type":"text","text":"Deux erreurs"}]}
        ]}]
        records=importer.parse_export(payload(data),"claude.json")
        self.assertEqual(records[0]["source"],"Claude")
        self.assertEqual(records[0]["messages"][1]["content"],"Deux erreurs")

    def test_zip_conversations(self):
        data=[{"title":"ZIP test","current_node":"node","mapping":{
            "node":{"parent":None,"message":{"author":{"role":"user"},"content":{"parts":["Import ok"]}}}
        }}]
        buf=io.BytesIO()
        with zipfile.ZipFile(buf,"w") as archive:
            archive.writestr("export/conversations.json",json.dumps(data))
        output=importer.preview(base64.b64encode(buf.getvalue()).decode(),"archive.zip")
        self.assertEqual(output["count"],1)

    def test_reject_unsupported_and_large_exports(self):
        with self.assertRaises(ValueError):
            importer.parse_export(payload({"foo":"bar"}),"other.json")
        with self.assertRaises(ValueError):
            importer.preview("not-base64!","export.json")
        with self.assertRaises(ValueError):
            importer.preview(payload([]),"export.json")

    def test_preview_does_not_modify_database_and_import_is_selected(self):
        source=[{"name":"Première","chat_messages":[{"sender":"human","text":"A"}]},
                {"name":"Deuxième","chat_messages":[{"sender":"assistant","text":"B"}]}]
        previous=server.DB
        try:
            with tempfile.TemporaryDirectory() as d:
                server.DB=Path(d)/"test.sqlite3"
                server.setup()
                pid=server.query("SELECT id FROM projects")[0]["id"]
                chats_before=len(server.query("SELECT id FROM chats"))
                template_chat=server.query("SELECT id FROM chats")[0]["id"]
                preview=importer.preview(payload(source),"claude.json")
                self.assertEqual(len(server.query("SELECT id FROM chats")),chats_before)
                self.assertEqual(preview["count"],2)
                result=importer.import_selected(server,pid,payload(source),"claude.json",["1"],template_chat=template_chat)
                self.assertEqual(result["count"],1)
                self.assertEqual(len(server.query("SELECT id FROM chats")),chats_before+1)
                imported=server.query("SELECT * FROM import_origins")
                self.assertEqual(imported[0]["source"],"Claude")
                messages=server.history(result["imported"][0]["id"])
                self.assertEqual(messages[0]["content"],"B")
                self.assertEqual(len(server.agents(result["imported"][0]["id"])),3)
        finally:
            server.DB=previous

    def test_refuse_invalid_selection(self):
        with self.assertRaises(ValueError):
            importer.import_selected(server,"missing",payload([]),"claude.json",["1","1"])


if __name__=="__main__":
    unittest.main()

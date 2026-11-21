import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import server
import web_workspace as web
import features_v9 as modes
import backup_v9


class WebWorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.old=server.DB
        server.DB=Path(self.tmp.name)/'db.sqlite3';server.setup()
        self.pid=server.one('SELECT id FROM projects')['id'];self.cid=server.one('SELECT id FROM chats')['id']

    def tearDown(self):server.DB=self.old;self.tmp.cleanup()

    def test_web_mode_never_calls_provider(self):
        modes.set_mode(server,self.pid,'web')
        with patch.object(server,'http') as request,patch.object(server.connections,'key') as key:
            for provider in ('openai','ollama','demo'):
                with self.assertRaises(ValueError):server.generate(provider,'test',[{'role':'system','content':'test'}],self.pid)
            request.assert_not_called();key.assert_not_called()
        self.assertTrue(all(x['skipped'] for x in server.group_round(self.cid)))
        modes.set_mode(server,self.pid,'local');self.assertEqual(modes.policy(server,self.pid)['mode'],'local')
        modes.set_mode(server,self.pid,'api');self.assertEqual(modes.policy(server,self.pid)['mode'],'api')

    def test_prepares_only_explicit_history(self):
        server.add(self.cid,'Vous','ancienne décision');self.assertEqual(web.prepare_prompt(server,self.cid,'nouvelle question'),'nouvelle question')
        result=web.prepare_prompt(server,self.cid,'nouvelle question',True)
        self.assertIn('ancienne décision',result);self.assertIn('nouvelle question',result)
        self.assertEqual(len(server.history(self.cid)),1)

    def test_manual_import_has_provenance(self):
        web.save_manual_response(server,self.cid,'chatgpt','Réponse copiée')
        self.assertEqual(server.history(self.cid)[-1]['speaker'],'Web · ChatGPT (import manuel)')
        with self.assertRaises(ValueError):web.save_manual_response(server,self.cid,'unknown','x')

    def test_old_backup_compatible_and_web_not_restored(self):
        modes.set_mode(server,self.pid,'web');payload=backup_v9.export_backup(server)
        payload['tables'].pop('project_web_modes')
        self.assertEqual(backup_v9.restore_backup(server,payload)['projects'],1)
        new=server.one('SELECT id FROM projects WHERE id!=?',(self.pid,))['id']
        self.assertEqual(modes.policy(server,new)['mode'],'local')

    def test_web_services_allowlisted(self):
        urls={x['url'] for x in web.provider_list()}
        self.assertEqual(urls,{'https://chatgpt.com/','https://claude.ai/','https://gemini.google.com/','https://chat.mistral.ai/'})

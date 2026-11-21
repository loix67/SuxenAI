import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import batch
import server
import workspace_v7 as w
import github_workflow as gh


class WorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.original=server.DB
        server.DB=Path(self.tmp.name)/'test.sqlite3'
        server.setup()
        self.pid=server.one('SELECT id FROM projects')['id']

    def tearDown(self):
        server.DB=self.original
        self.tmp.cleanup()

    def test_private_until_shared_and_project_scope(self):
        ident=w.save_item(server,self.pid,'memory','decision','local-only')
        self.assertEqual(w.context(server,self.pid),'')
        server.write('UPDATE workspace_items SET shared=1 WHERE id=?',(ident,))
        self.assertIn('local-only',w.context(server,self.pid))
        self.assertEqual(w.context(server,'other'),'')

    def test_project_roundtrip_private(self):
        w.save_item(server,self.pid,'document','notes.txt','hello',True)
        exported=w.export_project(server,self.pid)
        new=w.import_project(server,exported)
        self.assertNotEqual(new,self.pid)
        self.assertEqual(w.context(server,new),'')
        self.assertEqual(w.export_project(server,new)['items'],exported['items'])

    def test_invalid_import_atomic(self):
        exported=w.export_project(server,self.pid)
        exported['items']=[{'kind':'document','name':'../secret','content':'x'}]
        with self.assertRaises(ValueError): w.import_project(server,exported)
        self.assertEqual(len(server.query('SELECT id FROM projects')),1)

    def test_static_no_execution(self):
        self.assertEqual(w.static_checks('a.py','raise RuntimeError()')['status'],'passed')
        self.assertEqual(w.static_checks('a.py','def broken(')['status'],'failed')
        self.assertEqual(w.static_checks('a.json','{')['status'],'failed')
        self.assertIn('+new',w.diff('old\n','new\n','a.py'))


class BatchTests(unittest.TestCase):
    def test_exact_paths(self):
        snapshots=[{'path':'a.py','content':'x=1'},{'path':'b.py','content':'y=1'}]
        with self.assertRaises(ValueError):batch.parse_changes('{"a.py":"x=2"}',snapshots)
        self.assertEqual(len(batch.parse_changes('{"a.py":"x=2","b.py":"y=2"}',snapshots)),2)
        with self.assertRaises(ValueError):batch.paths_from(['a','a'])
        with self.assertRaises(ValueError):batch.paths_from(['../a'])

    def test_stale_source_stops_before_writes(self):
        files=[{'path':'a.py','content':'old','proposed':'new','sha':'oldsha'}]
        with patch.object(gh,'github_get',side_effect=[{'default_branch':'main'},{'object':{'sha':'head'}},{'tree':{'sha':'tree'}},{'sha':'changed'}]),patch.object(gh,'github_write') as write:
            with self.assertRaises(ValueError):gh.publish_batch('owner/repo',files,'suxenai/batch','title','body')
            write.assert_not_called()

    def test_publish_atomic_draft(self):
        files=[{'path':'a.py','content':'old','proposed':'new','sha':'oldsha'}]
        with patch.object(gh,'github_get',side_effect=[{'default_branch':'main'},{'object':{'sha':'head'}},{'tree':{'sha':'tree'}},{'sha':'oldsha'}]),patch.object(gh,'github_write',side_effect=[{'sha':'newtree'},{'sha':'commit'},{},{'html_url':'https://github.com/owner/repo/pull/1'}]) as write:
            result=gh.publish_batch('owner/repo',files,'suxenai/batch','title','body')
            self.assertEqual(result['commit_sha'],'commit')
            self.assertTrue(write.call_args_list[-1].args[2]['draft'])
            self.assertEqual(write.call_args_list[-2].args[2]['ref'],'refs/heads/suxenai/batch')

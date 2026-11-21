import base64
import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch
import server
import features_v9 as v9
import documents_v9 as docs
import backup_v9 as backup
import batch
import github_workflow as gh
import repository


class V9Tests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.old=server.DB
        server.DB=Path(self.temp.name)/'db.sqlite3';server.setup()
        self.pid=server.one('SELECT id FROM projects')['id'];self.cid=server.one('SELECT id FROM chats')['id']

    def tearDown(self):server.DB=self.old;self.temp.cleanup()

    def test_local_mode_blocks_cloud_before_reading_key(self):
        v9.set_policy(server,self.pid,True,False)
        with patch.object(server.connections,'key') as key,patch.object(server,'http') as http:
            with self.assertRaises(ValueError):server.generate('openai','gpt',[{'role':'system','content':'x'}],self.pid)
            key.assert_not_called();http.assert_not_called()
        out=server.group_round(self.cid)
        self.assertTrue(all(x['skipped'] for x in out))

    def test_usage_estimate_unknown_and_known(self):
        v9.record_usage(server,self.pid,'openai','x',{'usage':{'prompt_tokens':100,'completion_tokens':50}})
        v9.save_rate(server,'openai','x',2,4)
        v9.record_usage(server,self.pid,'openai','x',{'usage':{'prompt_tokens':100,'completion_tokens':50}})
        r=v9.usage_report(server,self.pid)[0]
        self.assertEqual(r['input_tokens'],200);self.assertEqual(r['unpriced'],1);self.assertAlmostEqual(r['estimated_usd'],.0004)

    def test_recall_is_project_scoped(self):
        cid=server.uid();server.write('INSERT INTO chats VALUES(?,?,?,?,?,?,?)',(cid,self.pid,'autre',None,'free','',server.now()));server.add(cid,'Vous','Décision architecture locale')
        self.assertEqual(v9.recall(server,self.pid,self.cid,'architecture')[0]['title'],'autre')
        self.assertEqual(v9.recall(server,'unknown',self.cid,'architecture'),[])

    def test_backup_restore_adds_private_copy(self):
        server.add(self.cid,'Vous','test sauvegarde')
        server.workspace_v7.save_item(server,self.pid,'memory','notes','privé',True)
        payload=backup.export_backup(server)
        self.assertNotIn('API_KEY',json.dumps(payload))
        self.assertEqual(backup.restore_backup(server,payload)['projects'],1)
        new=server.one('SELECT id FROM projects WHERE id!=?',(self.pid,))['id']
        self.assertEqual(v9.policy(server,new)['local_only'],1)
        self.assertEqual(server.workspace_v7.context(server,new),'')
        self.assertEqual(len(server.query('SELECT * FROM messages')),2)

    def test_backup_invalid_rolls_back(self):
        payload=backup.export_backup(server);payload['tables']['agents'][0]['chat']='missing'
        with self.assertRaises(ValueError):backup.restore_backup(server,payload)
        self.assertEqual(len(server.query('SELECT * FROM projects')),1)

    def test_docs_text_and_zip_local(self):
        self.assertEqual(docs.extract('a.txt',base64.b64encode(b'hello').decode()),'hello')
        raw=io.BytesIO()
        with zipfile.ZipFile(raw,'w') as z:z.writestr('word/document.xml','<w:document xmlns:w="w"><w:p><w:r><w:t>Bonjour</w:t></w:r></w:p></w:document>')
        self.assertEqual(docs.extract('a.docx',base64.b64encode(raw.getvalue()).decode()),'Bonjour')
        raw=io.BytesIO()
        with zipfile.ZipFile(raw,'w') as z:z.writestr('xl/worksheets/sheet1.xml','<worksheet xmlns="x"><row><c r="A1"><v>42</v></c></row></worksheet>')
        self.assertIn('A1: 42',docs.extract('a.xlsx',base64.b64encode(raw.getvalue()).decode()))

    def test_pdf_extract(self):
        try:
            from pypdf import PdfWriter
            from pypdf.generic import DictionaryObject,NameObject,DecodedStreamObject
        except ImportError:self.skipTest('pypdf available in packaged build')
        writer=PdfWriter();page=writer.add_blank_page(width=200,height=200)
        font=DictionaryObject({NameObject('/Type'):NameObject('/Font'),NameObject('/Subtype'):NameObject('/Type1'),NameObject('/BaseFont'):NameObject('/Helvetica')})
        page[NameObject('/Resources')]=DictionaryObject({NameObject('/Font'):DictionaryObject({NameObject('/F1'):font})})
        stream=DecodedStreamObject();stream.set_data(b'BT /F1 12 Tf 10 100 Td (Bonjour PDF) Tj ET');page[NameObject('/Contents')]=writer._add_object(stream)
        raw=io.BytesIO();writer.write(raw)
        self.assertIn('Bonjour PDF',docs.extract('test.pdf',base64.b64encode(raw.getvalue()).decode()))

    def test_new_files_must_not_overwrite(self):
        with self.assertRaises(ValueError):repository.ensure_new_path({'tree':[{'path':'existing','type':'blob'}]},'existing/sub.py')
        with self.assertRaises(ValueError):repository.ensure_new_path({'truncated':True},'new.py')
        repository.ensure_new_path({'tree':[{'path':'src','type':'tree'}]},'src/new.py')
        files=[{'path':'new.py','content':'','proposed':'x=1','sha':''}]
        with patch.object(gh,'github_get',side_effect=[{'default_branch':'main'},{'object':{'sha':'head'}},{'tree':{'sha':'tree'}},{'tree':[{'path':'new.py','type':'blob'}]}]),patch.object(gh,'github_write') as write:
            with self.assertRaises(ValueError):gh.publish_batch('owner/repo',files,'suxenai/batch','title','body')
            write.assert_not_called()

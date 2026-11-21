import json
import os
import unittest
from unittest.mock import MagicMock, patch
import connections
import server


class ConnectionTests(unittest.TestCase):
    def test_secret_storage_uses_only_keychain(self):
        with patch.object(connections,'credential_store') as backend:
            connections.save('openai','test-example-key')
            backend.return_value.set.assert_called_once_with('openai','test-example-key')
            connections.remove('openai')
            backend.return_value.delete.assert_called_once_with('openai')

    def test_invalid_provider_and_key(self):
        with patch.object(connections,'credential_store') as backend:
            for provider,secret in [('unknown','example-key'),('openai','bad'),('openai','example\nkey'),('openai',None)]:
                with self.assertRaises(ValueError):connections.save(provider,secret)
            backend.assert_not_called()

    def test_environment_priority_and_status_never_exposes_key(self):
        with patch.dict(os.environ,{'OPENAI_API_KEY':'test-env-secret'}),patch.object(connections,'credential_store') as backend:
            self.assertEqual(connections.key('openai'),'test-env-secret')
            self.assertEqual(connections.status('openai'),{'configured':True,'source':'environment'})
            backend.assert_not_called()

    def test_readonly_validation_no_chat(self):
        with patch.object(connections,'key',return_value='test-secret'),patch.object(connections.urllib.request,'build_opener') as factory:
            self.assertEqual(connections.test('openai'),{'ok':True})
            request=factory.return_value.open.call_args.args[0]
            self.assertEqual(request.full_url,'https://api.openai.com/v1/models')
            self.assertEqual(request.get_method(),'GET')
            self.assertIsNone(request.data)

    def test_ollama_models(self):
        with patch.object(connections.urllib.request,'build_opener') as factory:
            response=factory.return_value.open.return_value.__enter__.return_value
            response.read.return_value=json.dumps({'models':[{'name':'local-model'}]}).encode()
            self.assertEqual(connections.test('ollama'),{'ok':True,'models':['local-model']})

    def test_generation_uses_saved_credential(self):
        with patch.object(connections,'key',return_value='test-secret'),patch.object(server,'http',return_value={'choices':[{'message':{'content':'ok'}}]}) as http:
            self.assertEqual(server.generate('openai','model',[{'role':'system','content':'test'}]),'ok')
            self.assertEqual(http.call_args.args[2]['Authorization'],'Bearer test-secret')

    def test_reject_nonlocal_host(self):
        handler=MagicMock(spec=server.Handler)
        handler.headers={'Host':'example.org'}
        self.assertFalse(server.Handler.local_host(handler))
        handler.headers={'Host':f'127.0.0.1:{server.PORT}'}
        self.assertTrue(server.Handler.local_host(handler))

    def test_desktop_secret_required(self):
        handler=MagicMock(spec=server.Handler)
        with patch.object(server,'DESKTOP_TOKEN','test-desktop-token'):
            handler.headers={};self.assertFalse(server.Handler.desktop_authorized(handler))
            handler.headers={'X-SuxenAI-Desktop':'wrong'};self.assertFalse(server.Handler.desktop_authorized(handler))
            handler.headers={'X-SuxenAI-Desktop':'test-desktop-token'};self.assertTrue(server.Handler.desktop_authorized(handler))

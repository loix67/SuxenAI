import os
import tempfile
import unittest
from pathlib import Path

class SuxenAITest(unittest.TestCase):
    def test_database_and_group(self):
        import server
        original=server.DB
        try:
            with tempfile.TemporaryDirectory() as path:
                server.DB=Path(path)/"test.sqlite3"
                server.setup()
                projects=server.query("SELECT * FROM projects")
                self.assertEqual(len(projects),1)
                chat=server.query("SELECT * FROM chats")[0]
                team=server.agents(chat["id"])
                self.assertEqual(len(team),3)
                self.assertEqual(chat["mode"],"free")
                server.add(chat["id"],"Vous","Discutez d'une idée")
                self.assertEqual(len(server.history(chat["id"])),1)
                demo=dict(team[0],provider="demo",model="demo")
                turns=server.model_turns(chat["id"],demo)
                self.assertIn("Vous : Discutez",turns[-1]["content"])
                self.assertIn("DÉMONSTRATION",server.generate("demo","demo",turns))
        finally:
            server.DB=original

if __name__=="__main__":
    unittest.main()

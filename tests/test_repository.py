import base64
import json
import unittest
from unittest.mock import patch

import repository


class RepositoryTests(unittest.TestCase):
    def test_parse_github_https_and_shortcut(self):
        self.assertEqual(repository.parse_repo("https://github.com/example/my-repo"), ("example", "my-repo"))
        self.assertEqual(repository.parse_repo("example/my-repo"), ("example", "my-repo"))
        self.assertEqual(repository.parse_repo("https://github.com/example/my-repo.git"), ("example", "my-repo"))

    def test_reject_other_hosts_and_unsafe_paths(self):
        for url in ("https://evil.example/example/repo", "http://github.com/example/repo", "https://github.com/example/repo/tree/main"):
            with self.assertRaises(ValueError): repository.parse_repo(url)
        for path in ("../secret.txt", "src/../secret", "/etc/passwd", ".env", "keys/id_ed25519", "private/server.key"):
            with self.assertRaises(ValueError): repository.validate_path(path)

    @patch.object(repository, "github_get")
    def test_file_decoded_without_checkout(self, get):
        raw=b"print('hello')\n"
        get.side_effect=[
            {"full_name":"example/repo","default_branch":"main","private":False},
            {"type":"file","size":len(raw),"encoding":"base64","content":base64.b64encode(raw).decode(),"sha":"abc"}
        ]
        result=repository.repository_file("example/repo","src/main.py")
        self.assertEqual(result["content"],"print('hello')\n")
        self.assertEqual(result["sha"],"abc")
        self.assertEqual(get.call_count,2)

    @patch.object(repository,"github_get")
    def test_tree_excludes_binary_size_and_sensitive_names(self,get):
        get.side_effect=[
            {"full_name":"example/repo","default_branch":"main","private":False},
            {"tree":[
                {"path":"src/main.py","type":"blob","size":1024,"sha":"1"},
                {"path":".env","type":"blob","size":30,"sha":"2"},
                {"path":"media/movie.mp4","type":"blob","size":200000,"sha":"3"}
            ],"truncated":False}
        ]
        out=repository.repository_tree("example/repo")
        self.assertEqual([x["path"] for x in out["files"]],["src/main.py"])

if __name__=="__main__":unittest.main()

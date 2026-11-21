import json
import unittest
from unittest.mock import patch

import github_workflow
import workbench


class WorkbenchTests(unittest.TestCase):
    def test_extract_valid_model_json(self):
        content = workbench.extract_proposal('```json\n{"content":"print(42)\\n"}\n```')
        self.assertEqual(content, "print(42)\n")

    def test_reject_invalid_model_output(self):
        with self.assertRaises(ValueError):
            workbench.extract_proposal("I updated the file.")
        with self.assertRaises(ValueError):
            workbench.extract_proposal('{"content":null}')
        with self.assertRaises(ValueError):
            workbench.extract_proposal('{"content":"\\u0000"}')

    def test_protect_main_and_paths(self):
        for branch in ("main","master","feature/test","suxenai/../../main","suxenai/evil.lock","suxenai//double"):
            with self.assertRaises(ValueError):
                github_workflow.safe_branch(branch)
        self.assertEqual(github_workflow.safe_branch("suxenai/fix-123"),"suxenai/fix-123")

    @patch.object(github_workflow, "github_write")
    @patch.object(github_workflow, "github_get")
    def test_publish_creates_isolated_draft_pr(self, get, write):
        get.side_effect = [
            {"default_branch": "main"},
            {"object": {"sha":"commit123"}},
            {"sha":"old-sha"},
        ]
        write.side_effect = [{}, {"commit":{"sha":"newsha"}}, {"number":7,"html_url":"https://github.com/u/r/pull/7"}]
        result = github_workflow.publish("https://github.com/u/r","src/file.py",
            "print(2)\n","old-sha","suxenai/feature-7","Feature","Reviewed")
        self.assertEqual(result["pr_number"],7)
        self.assertEqual(write.call_count,3)
        self.assertEqual(write.call_args_list[-1].args[2]["draft"],True)
        self.assertEqual(write.call_args_list[-1].args[2]["base"],"main")

    @patch.object(github_workflow, "github_write")
    @patch.object(github_workflow, "github_get")
    def test_reject_stale_file_without_writing(self,get,write):
        get.side_effect=[
            {"default_branch":"main"},
            {"object":{"sha":"commit123"}},
            {"sha":"changed-sha"},
        ]
        with self.assertRaisesRegex(ValueError,"changé"):
            github_workflow.publish("u/r","src/file.py","new","old-sha",
                "suxenai/feature-8","Title","Review")
        write.assert_not_called()

    @patch.object(github_workflow,"github_get")
    def test_ci_without_checks_is_explicit(self,get):
        get.side_effect=[
            {"head":{"sha":"sha123"}},
            {"check_runs":[]},
        ]
        result=github_workflow.ci_status("u/r",3)
        self.assertFalse(result["has_checks"])
        self.assertIn("Aucun test",result["message"])


if __name__=="__main__":
    unittest.main()

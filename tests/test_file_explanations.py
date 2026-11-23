import json
import unittest
from unittest.mock import patch

import test_lumen as base
from lumen import assistant


class FileExplanationTests(unittest.TestCase):
    def setUp(self):
        self.report=base.demo_reports()[0]
        self.file=next(file for file in self.report["files"] if file["name"]=="package.json")

    def test_explicit_file_explanation_has_file_evidence(self):
        result=assistant.answer(self.report,"Explain this file",file_id=self.file["id"])
        self.assertEqual(result["file_references"],[self.file["id"]])
        self.assertEqual(result["references"],[])
        self.assertIn("package manifest",result["answer"])
        self.assertIn("Last human-opened time is unknown",result["answer"])

    def test_named_unflagged_file_is_found(self):
        result=assistant.answer(self.report,"What does package.json do?")
        self.assertEqual(result["file_references"],[self.file["id"]])

    def test_substring_is_not_mistaken_for_file_name(self):
        self.file["name"]="cope"
        result=assistant.answer(self.report,"What is the scope?")
        self.assertFalse(result.get("file_references"))

    def test_local_model_file_citation_and_masked_context(self):
        captured={}
        def response(path,data=None,timeout=4):
            if path=="/api/tags":return {"models":[{"name":"test-local"}]}
            if path=="/api/show":return {}
            captured.update(data)
            return {"message":{"content":json.dumps({"answer":"This is a package manifest.","references":[self.file["id"],"invented"]})}}
        with patch.object(assistant,"ollama_request",side_effect=response):
            result=assistant.answer(self.report,"Explain this file","test-local",file_id=self.file["id"])
        self.assertEqual(result["file_references"],[self.file["id"]])
        self.assertEqual(result["references"],[])
        self.assertNotIn("C:/Users/Alex",json.dumps(captured))
        self.assertIn("package manifest",captured["messages"][1]["content"])

    def test_unusable_model_capabilities_fail_before_inference(self):
        for capabilities in (None, "completion", [None], ["embedding"]):
            with self.subTest(capabilities=capabilities):
                def response(path, data=None, timeout=4):
                    if path == "/api/tags":
                        return {"models": [{"name": "test-local"}]}
                    if path == "/api/show":
                        return {"capabilities": capabilities}
                    self.fail("Unusable model should not receive an inference request")
                with patch.object(assistant, "ollama_request", side_effect=response):
                    with self.assertRaises(ValueError):
                        assistant.answer(self.report, "Explain", "test-local")


class FileEndpointTests(base.ServerFixtureCase):
    def test_unknown_file_rejected(self):
        status,_,_=self.request("POST","/api/ask",{"question":"Explain","file_id":"missing"})
        self.assertEqual(status,400)

    def test_file_explanation_endpoint(self):
        report=self.server.app.report("demo-current")
        file=report["files"][0]
        status,body,_=self.request("POST","/api/ask",{"question":"Explain","file_id":file["id"]})
        self.assertEqual(status,200)
        self.assertEqual(json.loads(body)["result"]["file_references"],[file["id"]])

    def test_ambiguous_file_and_finding_rejected(self):
        report=self.server.app.report("demo-current")
        status,_,_=self.request("POST","/api/ask",{"question":"Explain","file_id":report["files"][0]["id"],"finding_id":report["findings"][0]["id"]})
        self.assertEqual(status,400)

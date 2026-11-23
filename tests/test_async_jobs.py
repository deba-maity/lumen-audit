"""Exercise local-model job state without contacting or installing a model."""
import json
import threading
import time
from unittest.mock import patch

import test_lumen as base


class AnswerJobTests(base.ServerFixtureCase):
    def wait_for_job(self, identifier):
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline:
            status, raw, _ = self.request("GET", "/api/answers/" + identifier)
            self.assertEqual(status, 200)
            job = json.loads(raw)
            if job["status"] != "running":
                return job
            time.sleep(.01)
        self.fail("Fixture answer job did not finish")

    def test_only_one_model_job_runs_and_the_result_is_pollable(self):
        entered, release = threading.Event(), threading.Event()
        expected = {"answer": "Fixture explanation", "references": [], "source": "ollama"}
        def answer(*args):
            entered.set()
            if not release.wait(3):
                raise RuntimeError("Fixture release timed out")
            return expected
        with patch("lumen.server.answer", side_effect=answer):
            try:
                status, raw, _ = self.request("POST", "/api/ask", {"question": "Explain", "model": "fixture-model"})
                self.assertEqual(status, 200)
                identifier = json.loads(raw)["job_id"]
                self.assertTrue(entered.wait(2))
                status, _, _ = self.request("POST", "/api/ask", {"question": "Explain again", "model": "fixture-model"})
                self.assertEqual(status, 400)
            finally:
                release.set()
            job = self.wait_for_job(identifier)
            self.assertEqual(job["status"], "complete")
            self.assertEqual(job["result"], expected)

    def test_failed_model_releases_the_slot_for_a_retry(self):
        with patch("lumen.server.answer", side_effect=ValueError("Simulated invalid model response")):
            status, raw, _ = self.request("POST", "/api/ask", {"question": "Explain", "model": "fixture-model"})
            self.assertEqual(status, 200)
            job = self.wait_for_job(json.loads(raw)["job_id"])
            self.assertEqual(job["status"], "error")
            self.assertIn("invalid model", job["message"])
        expected = {"answer": "Retry succeeded", "references": [], "source": "ollama"}
        with patch("lumen.server.answer", return_value=expected):
            status, raw, _ = self.request("POST", "/api/ask", {"question": "Retry", "model": "fixture-model"})
            self.assertEqual(status, 200)
            job = self.wait_for_job(json.loads(raw)["job_id"])
            self.assertEqual(job["result"], expected)

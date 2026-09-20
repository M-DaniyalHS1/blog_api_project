import json
import io
import os
import unittest
from unittest.mock import patch, MagicMock
from urllib.error import URLError, HTTPError
from sqlalchemy.orm import Session
import test_articles
import chatbot
import model


class ChatTests(unittest.TestCase):
    setUp = test_articles.ArticleTests.setUp
    tearDown = test_articles.ArticleTests.tearDown

    @patch.dict(os.environ, {"OPENAI_API_KEY": "private-test-key"})
    @patch("chatbot.urlopen")
    def test_safe_provider_diagnostics(self, urlopen):
        self.post()
        for status, code, category in [(429, "insufficient_quota", "quota_exhausted_check_api_billing"), (401, "invalid_api_key", "authentication_failed_check_api_key"), (404, "model_not_found", "not_found_check_model_access")]:
            body = json.dumps({"error": {"code": code, "message": "private-test-key"}}).encode()
            urlopen.side_effect = HTTPError("https://api.openai.com/v1/responses", status, "private-test-key", {}, io.BytesIO(body))
            with self.assertLogs("chatbot", level="WARNING") as logs:
                response = self.ask()
            self.assertEqual(response.status_code, 503)
            self.assertIn(category, " ".join(logs.output))
            self.assertNotIn("private-test-key", " ".join(logs.output) + response.text)

    def post(self, title="Space launch", status="published"):
        return self.client.post("/blogs", json={"title": title, "content": "The launch took place on Monday.", "status": status}).json()["id"]

    def ask(self, **kwargs):
        return self.client.post("/chat", json={"question": "Space launch", **kwargs})

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    @patch("chatbot.generate_answer")
    def test_public_sources_and_draft_exclusion(self, generate):
        public = self.post()
        draft = self.post("Space launch secret", "draft")
        generate.return_value = chatbot.ModelAnswer(answer="The post says Monday.", source_ids=[public], insufficient_context=False)
        result = self.ask()
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json()["sources"], [{"id": public, "title": "Space launch", "url": f"#/posts/{public}"}])
        self.assertEqual([s["id"] for s in generate.call_args.args[1]], [public])
        generate.reset_mock()
        self.assertEqual(self.ask(article_id=draft).json(), chatbot.FALLBACK)
        generate.assert_not_called()

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    @patch("chatbot.generate_answer")
    def test_invalid_citations_and_insufficient_evidence(self, generate):
        self.post()
        for ids, insufficient in [([99999], False), ([], False), ([1], True)]:
            generate.return_value = chatbot.ModelAnswer(answer="Unsupported answer", source_ids=ids, insufficient_context=insufficient)
            self.assertEqual(self.ask().json(), chatbot.FALLBACK)
        generate.reset_mock()
        self.assertEqual(self.ask(question="Unrelated zebras").json(), chatbot.FALLBACK)
        generate.assert_not_called()

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    @patch("chatbot.generate_answer")
    def test_unpublished_during_response(self, generate):
        id = self.post()
        def unpublish(*args):
            with Session(self.engine) as db:
                db.get(model.Blog, id).status = "draft"
                db.commit()
            return chatbot.ModelAnswer(answer="Monday", source_ids=[id], insufficient_context=False)
        generate.side_effect = unpublish
        self.assertEqual(self.ask().json(), chatbot.FALLBACK)

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key", "CHAT_DAILY_LIMIT": "2", "CHAT_HOURLY_LIMIT": "10"})
    def test_shared_limit_persists_across_requests(self):
        self.assertEqual(self.ask().status_code, 200)
        self.assertEqual(self.ask().status_code, 200)
        response = self.ask()
        self.assertEqual(response.status_code, 429)
        self.assertIn("Retry-After", response.headers)

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key", "CHAT_DAILY_LIMIT": "100", "CHAT_HOURLY_LIMIT": "1"})
    def test_reader_limit(self):
        self.assertEqual(self.ask().status_code, 200)
        self.assertEqual(self.ask().status_code, 429)

    @patch.dict(os.environ, {"OPENAI_API_KEY": ""})
    def test_configuration_and_input_errors(self):
        self.assertEqual(self.ask().status_code, 503)
        for question in [" ", "x" * 1001]:
            self.assertEqual(self.ask(question=question).status_code, 422)
        self.assertEqual(self.ask(article_id=-1).status_code, 422)

    @patch.dict(os.environ, {"OPENAI_API_KEY": "private-test-key"})
    @patch("chatbot.urlopen")
    def test_provider_contract_and_errors(self, urlopen):
        id = self.post()
        response = MagicMock()
        response.read.return_value = json.dumps({"status": "completed", "output": [{"type": "message", "content": [{"type": "output_text", "text": json.dumps({"answer": "Monday", "source_ids": [id], "insufficient_context": False})}]}]}).encode()
        urlopen.return_value.__enter__.return_value = response
        self.assertEqual(self.ask().json()["answer"], "Monday")
        request = urlopen.call_args.args[0]
        payload = json.loads(request.data)
        self.assertFalse(payload["store"])
        self.assertEqual(payload["text"]["format"]["type"], "json_schema")
        self.assertEqual(payload["max_output_tokens"], 900)
        self.assertNotIn("tools", payload)
        for failure in [URLError("private-test-key"), TimeoutError("secret")]:
            urlopen.side_effect = failure
            result = self.ask()
            self.assertEqual(result.status_code, 503)
            self.assertNotIn("private-test-key", result.text)
        urlopen.side_effect = None
        response.read.return_value = b'{"status":"incomplete"}'
        self.assertEqual(self.ask().status_code, 503)


if __name__ == "__main__":
    unittest.main()

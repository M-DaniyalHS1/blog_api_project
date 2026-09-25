import json
import os
import unittest
from unittest.mock import patch
from sqlalchemy.orm import Session
import test_articles
import chatbot
import model


class ChatTests(unittest.TestCase):
    setUp = test_articles.ArticleTests.setUp
    tearDown = test_articles.ArticleTests.tearDown

    @patch.dict(os.environ, {"CHAT_PROVIDER": "gemini", "GEMINI_API_KEY": "gemini-test-key", "OPENAI_API_KEY": "must-not-use"})
    def test_gemini_agent_structured_answer(self):
        from unittest.mock import AsyncMock
        from openai.types.chat import ChatCompletion
        id = self.post()
        completion = ChatCompletion(id="test", created=0, model="gemini-test", object="chat.completion",
            choices=[{"index": 0, "finish_reason": "stop", "message": {"role": "assistant", "content": json.dumps({"answer": "Monday", "source_ids": [id], "insufficient_context": False})}}])
        client = AsyncMock()
        client.__aenter__.return_value = client
        client.chat.completions.create.return_value = completion
        with patch("chatbot.AsyncOpenAI", return_value=client) as factory, patch("chatbot.Runner.run", wraps=chatbot.Runner.run) as runner:
            result = self.ask()
        self.assertEqual(result.status_code, 200, result.text)
        self.assertEqual(result.json()["sources"][0]["id"], id)
        self.assertEqual(factory.call_args.kwargs["api_key"], "gemini-test-key")
        self.assertIn("generativelanguage.googleapis.com", factory.call_args.kwargs["base_url"])
        self.assertEqual(factory.call_args.kwargs["max_retries"], 0)
        self.assertTrue(runner.call_args.kwargs["run_config"].tracing_disabled)
        self.assertEqual(runner.call_args.kwargs["max_turns"], 1)
        payload = client.chat.completions.create.call_args.kwargs
        self.assertEqual(payload["response_format"]["type"], "json_schema")
        self.assertFalse(runner.call_args.args[0].tools)

    @patch.dict(os.environ, {"CHAT_PROVIDER": "gemini", "GEMINI_API_KEY": "gemini-test-key"})
    def test_agent_failure_is_redacted_and_retry_bounded(self):
        import httpx
        from openai import APIStatusError
        from unittest.mock import AsyncMock
        self.post()
        error = APIStatusError("private-test-key", response=httpx.Response(503, request=httpx.Request("POST", "https://example.test")), body={})
        with patch("chatbot.Runner.run", new_callable=AsyncMock, side_effect=error) as runner, patch("chatbot.asyncio.sleep", new_callable=AsyncMock):
            result = self.ask()
        self.assertEqual(result.status_code, 503)
        self.assertNotIn("private-test-key", result.text)
        self.assertEqual(runner.call_count, 2)

    @patch.dict(os.environ, {"CHAT_PROVIDER": "gemini", "GEMINI_API_KEY": "", "OPENAI_API_KEY": "must-not-use"})
    def test_gemini_requires_its_own_key(self):
        self.assertEqual(self.ask().status_code, 503)

    def post(self, title="Space launch", status="published"):
        return self.client.post("/blogs", json={"title": title, "content": "The launch took place on Monday.", "status": status}).json()["id"]

    def ask(self, **kwargs):
        return self.client.post("/chat", json={"question": "Space launch", **kwargs})

    @patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"})
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

    @patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"})
    @patch("chatbot.generate_answer")
    def test_invalid_citations_and_insufficient_evidence(self, generate):
        self.post()
        for ids, insufficient in [([99999], False), ([], False), ([1], True)]:
            generate.return_value = chatbot.ModelAnswer(answer="Unsupported answer", source_ids=ids, insufficient_context=insufficient)
            self.assertEqual(self.ask().json(), chatbot.FALLBACK)
        generate.reset_mock()
        self.assertEqual(self.ask(question="Unrelated zebras").json(), chatbot.FALLBACK)
        generate.assert_not_called()

    @patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"})
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

    @patch.dict(os.environ, {"GEMINI_API_KEY": "test-key", "CHAT_DAILY_LIMIT": "2", "CHAT_HOURLY_LIMIT": "10"})
    def test_shared_limit_persists_across_requests(self):
        self.assertEqual(self.ask().status_code, 200)
        self.assertEqual(self.ask().status_code, 200)
        response = self.ask()
        self.assertEqual(response.status_code, 429)
        self.assertIn("Retry-After", response.headers)

    @patch.dict(os.environ, {"GEMINI_API_KEY": "test-key", "CHAT_DAILY_LIMIT": "100", "CHAT_HOURLY_LIMIT": "1"})
    def test_reader_limit(self):
        self.assertEqual(self.ask().status_code, 200)
        self.assertEqual(self.ask().status_code, 429)

    @patch.dict(os.environ, {"GEMINI_API_KEY": ""})
    def test_configuration_and_input_errors(self):
        self.assertEqual(self.ask().status_code, 503)
        for question in [" ", "x" * 1001]:
            self.assertEqual(self.ask(question=question).status_code, 422)
        self.assertEqual(self.ask(article_id=-1).status_code, 422)

if __name__ == "__main__":
    unittest.main()

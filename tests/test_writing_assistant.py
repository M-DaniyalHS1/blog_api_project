import os
import unittest
from unittest.mock import patch, AsyncMock
from sqlalchemy.orm import Session
import test_accounts
import model
import writing_assistant as writing


@patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"})
class WritingTests(unittest.TestCase):
    setUp = test_accounts.AccountTests.setUp
    tearDown = test_accounts.AccountTests.tearDown
    register = test_accounts.AccountTests.register
    login = test_accounts.AccountTests.login

    def writer(self):
        self.register()
        return self.login()

    def ask(self, headers=None, **changes):
        return self.client.post("/writing-assistant", headers=headers or {}, json={"action": "summary", "title": "Launch", "content": "The launch happened on Monday.", **changes})

    @patch("writing_assistant.run_gemini_agent", new_callable=AsyncMock)
    def test_requires_login_and_ownership(self, agent):
        self.assertEqual(self.ask().status_code, 401)
        owner = self.writer()
        post = self.client.post("/blogs", headers=owner, json={"title": "Private", "content": "Secret", "status": "draft"}).json()
        self.register("other_writer")
        other = self.login("other_writer")
        self.assertEqual(self.ask(other, post_id=post["id"]).status_code, 404)
        self.assertEqual(self.ask(other, post_id=99999).status_code, 404)
        agent.assert_not_called()

    @patch("writing_assistant.run_gemini_agent", new_callable=AsyncMock)
    def test_all_actions_preserve_saved_draft(self, agent):
        headers = self.writer()
        post = self.client.post("/blogs", headers=headers, json={"title": "Original", "content": "Original text", "status": "draft"}).json()
        for action, output in [("titles", writing.TitleSuggestions(titles=["One", "Two", "Three"])), ("summary", writing.SummarySuggestion(summary="Short summary")), ("improve", writing.ArticleSuggestion(content="Improved article"))]:
            agent.return_value = output
            response = self.ask(headers, post_id=post["id"], action=action)
            self.assertEqual(response.status_code, 200, response.text)
            self.assertEqual(response.json()["suggestion"], output.model_dump())
            self.assertEqual(agent.call_args.kwargs["output_type"], type(output))
        with Session(self.engine) as db:
            saved = db.get(model.Blog, post["id"])
            self.assertEqual((saved.title, saved.content, saved.status), ("Original", "Original text", "draft"))
            self.assertEqual(db.query(model.Blog).count(), 1)

    @patch("writing_assistant.run_gemini_agent", new_callable=AsyncMock)
    def test_new_unsaved_article_and_provider_error(self, agent):
        headers = self.writer()
        agent.return_value = writing.SummarySuggestion(summary="Summary")
        self.assertEqual(self.ask(headers).status_code, 200)
        agent.side_effect = TimeoutError("private-secret")
        response = self.ask(headers)
        self.assertEqual(response.status_code, 503)
        self.assertNotIn("private-secret", response.text)
        with Session(self.engine) as db:
            self.assertEqual(db.query(model.Blog).count(), 0)

    @patch("writing_assistant.run_gemini_agent", new_callable=AsyncMock)
    def test_limits_and_invalid_input(self, agent):
        headers = self.writer()
        for changes in [{"content": " "}, {"content": "x" * 12001}, {"action": "publish"}, {"author_id": 1}]:
            self.assertEqual(self.ask(headers, **changes).status_code, 422)
        with patch.dict(os.environ, {"GEMINI_API_KEY": ""}):
            self.assertEqual(self.ask(headers).status_code, 503)
        with patch.dict(os.environ, {"CHAT_DAILY_LIMIT": "0"}):
            self.assertEqual(self.ask(headers).status_code, 429)
        agent.assert_not_called()

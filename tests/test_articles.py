"""Run in an isolated process: python -m unittest discover -s tests."""
import os
import unittest
from unittest.mock import patch

# Never connect to the real database or load real credentials in these tests.
os.environ.update(DATABASE_URL="sqlite://", SECRET_KEY="test-only-secret-" * 4,
                  ADMIN_USERNAME="test-admin", ADMIN_PASSWORD_HASH="unused-in-tests")
with patch("dotenv.load_dotenv"):
    import main

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import model


class ArticleTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        model.base.metadata.create_all(self.engine)
        session = sessionmaker(bind=self.engine)

        def db():
            with session() as connection:
                yield connection

        main.app.dependency_overrides[main.get_db] = db
        main.app.dependency_overrides[main.verify_token] = lambda: {"sub": "test-admin"}
        self.client = TestClient(main.app)

    def tearDown(self):
        self.client.close()
        main.app.dependency_overrides.clear()
        self.engine.dispose()

    def test_article_round_trip_and_date_preservation(self):
        created = self.client.post("/blogs", json={"title": "A story", "content": "First paragraph\n\nSecond paragraph", "source_url": "https://example.com/story"})
        self.assertEqual(created.status_code, 200)
        data = created.json()
        self.assertTrue(data["published_at"])
        fetched = self.client.get(f"/blogs/{data['id']}")
        self.assertEqual(fetched.json(), data)
        edited = self.client.put(f"/blogs/{data['id']}", json={"title": "Updated", "content": "New body"}).json()
        self.assertEqual(edited["published_at"], data["published_at"])
        self.assertEqual(edited["source_url"], data["source_url"])

    def test_missing_and_unsafe_source(self):
        self.assertEqual(self.client.get("/blogs/999").status_code, 404)
        response = self.client.post("/blogs", json={"title": "Test", "content": "Body", "source_url": "javascript:alert(1)"})
        self.assertEqual(response.status_code, 422)

    def test_optional_source_and_latest_first(self):
        for title in ("First", "Second"):
            self.client.post("/blogs", json={"title": title, "content": "Body"})
        rows = self.client.get("/blogs").json()["data"]
        self.assertEqual([row["title"] for row in rows], ["Second", "First"])
        self.assertIsNone(rows[0]["source_url"])


if __name__ == "__main__":
    unittest.main()

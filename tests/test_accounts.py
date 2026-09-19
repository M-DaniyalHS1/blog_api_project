import unittest
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import select
import test_articles
import main
import model
import auth
from account_setup import initialize_admin


class AccountTests(unittest.TestCase):
    def setUp(self):
        test_articles.ArticleTests.setUp(self)
        main.app.dependency_overrides.pop(main.current_user)

    def tearDown(self):
        test_articles.ArticleTests.tearDown(self)

    def register(self, name="reader_one"):
        return self.client.post("/register", json={"username": name, "password": "reader-password-123"})

    def login(self, name="reader_one"):
        response = self.client.post("/login", data={"username": name, "password": "reader-password-123"})
        self.assertEqual(response.status_code, 200)
        return {"Authorization": f"Bearer {response.json()['access_token']}"}

    def test_registration_validation_hash_and_duplicate(self):
        response = self.register(" Reader_One ")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["username"], "reader_one")
        self.assertEqual(set(response.json()), {"id", "username"})
        with Session(self.engine) as db:
            user = db.scalar(select(model.User).where(model.User.username == "reader_one"))
            self.assertNotEqual(user.password_hash, "reader-password-123")
            self.assertTrue(auth.verify_password("reader-password-123", user.password_hash))
            self.assertFalse(user.is_admin)
        self.assertEqual(self.register("READER_ONE").status_code, 409)
        self.assertEqual(self.register("ab").status_code, 422)
        self.assertEqual(self.client.post("/register", json={"username": "test-admin", "password": "reader-password-123"}).status_code, 422)
        self.assertEqual(self.client.post("/register", json={"username": "reader_two", "password": "short"}).status_code, 422)
        self.assertEqual(self.client.post("/register", json={"username": "reader_two", "password": "long-password", "is_admin": True}).status_code, 422)

    def test_login_failures_and_server_logout(self):
        self.register()
        for username, password in [("reader_one", "wrong"), ("missing", "reader-password-123")]:
            self.assertEqual(self.client.post("/login", data={"username": username, "password": password}).status_code, 401)
        headers = self.login("READER_ONE")
        self.assertEqual(self.client.get("/me", headers=headers).json()["username"], "reader_one")
        self.assertEqual(self.client.post("/logout", headers=headers).status_code, 204)
        self.assertEqual(self.client.get("/me", headers=headers).status_code, 401)
        self.assertEqual(self.client.get("/me", headers=self.login()).status_code, 200)

    def test_post_ownership_and_public_data(self):
        self.register("writer_one")
        self.register("writer_two")
        one, two = self.login("writer_one"), self.login("writer_two")
        body = {"title": "Owned story", "content": "Body", "author_id": 999}
        self.assertEqual(self.client.post("/blogs", json=body).status_code, 401)
        created = self.client.post("/blogs", json=body, headers=one)
        self.assertEqual(created.status_code, 200)
        post = created.json()
        self.assertEqual(post["author"]["username"], "writer_one")
        self.assertNotEqual(post["author_id"], 999)
        url = f"/blogs/{post['id']}"
        self.assertEqual(self.client.put(url, json=body, headers=two).status_code, 403)
        self.assertEqual(self.client.delete(url, headers=two).status_code, 403)
        self.assertEqual(self.client.put(url, json=body, headers=one).status_code, 200)
        feed = self.client.get("/blogs").json()
        self.assertNotIn("password_hash", str(feed))
        self.assertNotIn("token_version", str(feed))
        self.assertEqual(self.client.get(url).status_code, 200)
        self.assertEqual(self.client.delete(url, headers=one).status_code, 200)

    def test_expired_invalid_and_legacy_tokens(self):
        self.register()
        headers = self.login()
        token = headers["Authorization"].split()[1]
        payload = auth.jwt.decode(token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])
        payload["exp"] = datetime.now(timezone.utc) - timedelta(minutes=1)
        expired = auth.jwt.encode(payload, auth.SECRET_KEY, algorithm=auth.ALGORITHM)
        legacy = auth.jwt.encode({"sub": "test-admin", "exp": datetime.now(timezone.utc) + timedelta(minutes=5)}, auth.SECRET_KEY, algorithm=auth.ALGORITHM)
        for invalid in (expired, legacy, "invalid.token.value"):
            self.assertEqual(self.client.get("/me", headers={"Authorization": f"Bearer {invalid}"}).status_code, 401)

    def test_admin_bootstrap_is_idempotent_preserves_posts(self):
        with Session(self.engine) as db:
            legacy = model.Blog(title="Existing story", content="Keep this text")
            db.add(legacy)
            db.commit()
            admin_hash = auth.password_hash.hash("admin-test-password")
            admin = initialize_admin(db, "test-admin", admin_hash)
            admin_id = admin.id
            initialize_admin(db, "test-admin", admin_hash)
            db.refresh(legacy)
            self.assertEqual(legacy.author_id, admin_id)
            self.assertEqual(legacy.content, "Keep this text")
        response = self.client.post("/login", data={"username": "test-admin", "password": "admin-test-password"})
        self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main()

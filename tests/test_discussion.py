import unittest
from sqlalchemy.orm import Session
import test_accounts
import model


class DiscussionTests(unittest.TestCase):
    setUp = test_accounts.AccountTests.setUp
    tearDown = test_accounts.AccountTests.tearDown
    register = test_accounts.AccountTests.register
    login = test_accounts.AccountTests.login

    def story(self, headers, status="published"):
        result = self.client.post("/blogs", headers=headers, json={"title": "Story", "content": "Body", "status": status})
        self.assertEqual(result.status_code, 200)
        return result.json()["id"]

    def test_comments_ownership_validation_and_persistence(self):
        self.register("reader_one")
        self.register("reader_two")
        one, two = self.login("reader_one"), self.login("reader_two")
        post_id = self.story(one)
        base = f"/blogs/{post_id}/comments"
        self.assertEqual(self.client.post(base, json={"content": "Hello"}).status_code, 401)
        for content in ("  \n ", "x" * 2001):
            self.assertEqual(self.client.post(base, headers=one, json={"content": content}).status_code, 422)
        created = self.client.post(base, headers=one, json={"content": " First thought "})
        self.assertEqual(created.status_code, 201)
        comment = created.json()
        self.assertEqual(comment["content"], "First thought")
        self.assertNotIn("password_hash", comment["author"])
        item = f"{base}/{comment['id']}"
        self.assertEqual(self.client.put(item, headers=two, json={"content": "Hijack"}).status_code, 403)
        self.assertEqual(self.client.delete(item, headers=two).status_code, 403)
        edited = self.client.put(item, headers=one, json={"content": "Updated thought"}).json()
        self.assertTrue(edited["edited_at"])
        self.assertEqual(self.client.get(base).json()["data"][0]["content"], "Updated thought")
        other = self.story(one)
        self.assertEqual(self.client.put(f"/blogs/{other}/comments/{comment['id']}", headers=one, json={"content": "Wrong post"}).status_code, 404)
        self.assertEqual(self.client.delete(item, headers=one).status_code, 204)
        self.assertEqual(self.client.get(base).json()["total"], 0)

    def test_likes_are_idempotent_and_user_specific(self):
        self.register("reader_one")
        self.register("reader_two")
        one, two = self.login("reader_one"), self.login("reader_two")
        post_id = self.story(one)
        base = f"/blogs/{post_id}"
        self.assertEqual(self.client.put(base + "/like").status_code, 401)
        for _ in range(3):
            self.assertEqual(self.client.put(base + "/like", headers=one).json(), {"count": 1, "liked": True})
        self.assertEqual(self.client.get(base + "/reactions").json(), {"count": 1, "liked": False})
        self.assertTrue(self.client.get(base + "/reactions", headers=one).json()["liked"])
        self.client.put(base + "/like", headers=two)
        self.assertEqual(self.client.delete(base + "/like", headers=one).json(), {"count": 1, "liked": False})
        self.assertEqual(self.client.delete(base + "/like", headers=one).json()["count"], 1)
        self.assertTrue(self.client.get(base + "/reactions", headers=two).json()["liked"])

    def test_drafts_hide_discussion_and_post_delete_cleans_up(self):
        self.register()
        headers = self.login()
        post_id = self.story(headers)
        base = f"/blogs/{post_id}"
        comment = self.client.post(base + "/comments", headers=headers, json={"content": "Comment"}).json()
        self.client.put(base + "/like", headers=headers)
        self.client.put(base, headers=headers, json={"title": "Hidden", "content": "Body", "status": "draft"})
        for suffix in ("/comments", "/reactions"):
            self.assertEqual(self.client.get(base + suffix).status_code, 404)
        self.assertEqual(self.client.post(base + "/comments", headers=headers, json={"content": "No"}).status_code, 404)
        self.assertEqual(self.client.put(base + "/like", headers=headers).status_code, 404)
        self.assertEqual(self.client.delete(base + "/like", headers=headers).status_code, 404)
        self.assertEqual(self.client.delete(base + f"/comments/{comment['id']}", headers=headers).status_code, 404)
        self.assertEqual(self.client.delete(base, headers=headers).status_code, 200)
        with Session(self.engine) as db:
            self.assertEqual(db.query(model.Comment).count(), 0)
            self.assertEqual(db.query(model.Like).count(), 0)

    def test_comment_pagination_and_missing_post(self):
        self.register()
        headers = self.login()
        base = f"/blogs/{self.story(headers)}/comments"
        for index in range(11):
            self.client.post(base, headers=headers, json={"content": str(index)})
        first = self.client.get(base).json()
        second = self.client.get(base + "?page=2").json()
        self.assertEqual(first["total"], 11)
        self.assertEqual(len(first["data"]), 10)
        self.assertEqual(len(second["data"]), 1)
        self.assertFalse({c['id'] for c in first['data']} & {c['id'] for c in second['data']})
        self.assertEqual(self.client.get(base + "?page=0").status_code, 422)
        self.assertEqual(self.client.get("/blogs/999999/comments").status_code, 404)


if __name__ == "__main__":
    unittest.main()

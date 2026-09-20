import unittest
import test_accounts


class DraftTests(unittest.TestCase):
    setUp = test_accounts.AccountTests.setUp
    tearDown = test_accounts.AccountTests.tearDown
    register = test_accounts.AccountTests.register
    login = test_accounts.AccountTests.login

    def test_draft_privacy_and_publish_lifecycle(self):
        author = self.register().json()
        headers = self.login()
        draft = self.client.post("/blogs", headers=headers, json={"title": "Secret draft", "content": "", "status": "draft"}).json()
        self.assertIsNone(draft["published_at"])
        url = f"/blogs/{draft['id']}"
        self.assertEqual(self.client.get(url).status_code, 404)
        self.assertEqual(self.client.get(url, headers=headers).status_code, 404)
        self.assertEqual(self.client.get("/blogs?search=Secret").json()["total"], 0)
        self.assertEqual(self.client.get(f"/authors/{author['id']}").json()["total"], 0)
        self.assertEqual(self.client.get("/me/posts", headers=headers).json()["data"][0]["id"], draft["id"])
        self.assertEqual(self.client.put(url, headers=headers, json={"title": "News", "content": "", "status": "published"}).status_code, 422)
        published = self.client.put(url, headers=headers, json={"title": "News", "content": "Full story", "status": "published"}).json()
        self.assertTrue(published["published_at"])
        self.assertEqual(self.client.get(url).status_code, 200)
        self.assertEqual(self.client.get(f"/authors/{author['id']}").json()["total"], 1)
        self.client.put(url, headers=headers, json={"title": "News", "content": "Full story", "status": "draft"})
        self.assertEqual(self.client.get(url).status_code, 404)
        edited = self.client.put(url, headers=headers, json={"title": "Private revision", "content": "Body"}).json()
        self.assertEqual(edited["status"], "draft")
        republished = self.client.put(url, headers=headers, json={"title": "News", "content": "Full story", "status": "published"}).json()
        self.assertEqual(republished["published_at"], published["published_at"])

    def test_private_list_and_owner_only_mutations(self):
        self.register("writer_one")
        self.register("writer_two")
        one, two = self.login("writer_one"), self.login("writer_two")
        body = {"title": "Private", "content": "Body", "status": "draft"}
        draft = self.client.post("/blogs", headers=one, json=body).json()
        self.assertEqual(self.client.get("/me/posts").status_code, 401)
        self.assertEqual(self.client.get("/me/posts", headers=two).json()["total"], 0)
        url = f"/blogs/{draft['id']}"
        self.assertEqual(self.client.put(url, headers=two, json=body).status_code, 403)
        self.assertEqual(self.client.delete(url, headers=two).status_code, 403)
        self.assertEqual(self.client.delete(url, headers=one).status_code, 200)
        self.assertEqual(self.client.get("/me/posts", headers=one).json()["total"], 0)
        self.assertEqual(self.client.get(url).status_code, 404)


if __name__ == "__main__":
    unittest.main()

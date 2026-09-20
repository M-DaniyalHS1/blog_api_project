import unittest
import test_accounts


class ProfileTests(unittest.TestCase):
    setUp = test_accounts.AccountTests.setUp
    tearDown = test_accounts.AccountTests.tearDown
    register = test_accounts.AccountTests.register
    login = test_accounts.AccountTests.login

    def test_edit_own_profile_and_read_public(self):
        one = self.register("author_one").json()
        two = self.register("author_two").json()
        headers = self.login("author_one")
        fields = {"display_name": "Dani", "bio": "News and ideas\nSecond line", "avatar_url": "https://example.com/photo.jpg"}
        result = self.client.patch("/me/profile", json=fields, headers=headers)
        self.assertEqual(result.status_code, 200)
        public = self.client.get(f"/authors/{one['id']}").json()["author"]
        self.assertEqual(public["bio"], fields["bio"])
        self.assertEqual(public["display_name"], "Dani")
        self.assertNotIn("password_hash", public)
        self.assertNotIn("is_admin", public)
        self.assertIsNone(self.client.get(f"/authors/{two['id']}").json()["author"]["bio"])
        self.assertEqual(self.client.patch("/me/profile", json=fields).status_code, 401)
        self.assertEqual(self.client.patch("/me/profile", json={"id": two['id'], "bio": "Overwrite"}, headers=headers).status_code, 422)

    def test_validation_clear_and_partial_update(self):
        self.register()
        headers = self.login()
        self.assertEqual(self.client.patch("/me/profile", json={"avatar_url": "javascript:alert(1)"}, headers=headers).status_code, 422)
        self.assertEqual(self.client.patch("/me/profile", json={"bio": "x" * 1001}, headers=headers).status_code, 422)
        self.client.patch("/me/profile", json={"bio": "Keep", "display_name": "Writer"}, headers=headers)
        result = self.client.patch("/me/profile", json={"display_name": "   "}, headers=headers).json()
        self.assertIsNone(result["display_name"])
        self.assertEqual(result["bio"], "Keep")

    def test_author_posts_filter_and_pages(self):
        one = self.register("author_one").json()
        self.register("author_two")
        headers = self.login("author_one")
        for index in range(13):
            self.client.post("/blogs", json={"title": str(index), "content": "Body"}, headers=headers)
        self.client.post("/blogs", json={"title": "Other author", "content": "Body"}, headers=self.login("author_two"))
        first = self.client.get(f"/authors/{one['id']}").json()
        second = self.client.get(f"/authors/{one['id']}?page=2").json()
        self.assertEqual(first["total"], 13)
        self.assertEqual(len(first["data"]), 12)
        self.assertEqual(len(second["data"]), 1)
        self.assertEqual(first["data"][0]["title"], "12")
        self.assertEqual(self.client.get("/authors/99999").status_code, 404)
        self.assertEqual(self.client.get(f"/authors/{one['id']}?page=0").status_code, 422)


if __name__ == "__main__":
    unittest.main()

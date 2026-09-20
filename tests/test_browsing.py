import unittest
import test_accounts


class BrowsingTests(unittest.TestCase):
    setUp = test_accounts.AccountTests.setUp
    tearDown = test_accounts.AccountTests.tearDown
    register = test_accounts.AccountTests.register
    login = test_accounts.AccountTests.login

    def test_search_all_fields_categories_and_private_drafts(self):
        self.register()
        headers = self.login()
        for index in range(8):
            self.client.post("/blogs", headers=headers, json={"title": f"Story {index}", "content": "Body", "category": "News"})
        target = self.client.post("/blogs", headers=headers, json={"title": "Older relevant story", "summary": "Unique summary", "content": "Deep needle inside article", "category": "Technology"}).json()
        for index in range(8):
            self.client.post("/blogs", headers=headers, json={"title": f"New {index}", "content": "Body"})
        self.client.post("/blogs", headers=headers, json={"title": "needle secret", "content": "Unique summary", "category": "Technology", "status": "draft"})
        for search in ("NEEDLE", "Unique summary", "Older relevant"):
            result = self.client.get("/blogs", params={"search": search, "category": "Technology"}).json()
            self.assertEqual(result["total"], 1)
            self.assertEqual(result["data"][0]["id"], target["id"])
        self.assertEqual(self.client.get("/blogs", params={"search": "needle", "category": "News"}).json()["total"], 0)
        self.assertEqual(self.client.get("/blogs", params={"category": "News"}).json()["total"], 8)

    def test_pagination_validation_and_category_update(self):
        self.register()
        headers = self.login()
        for index in range(7):
            self.client.post("/blogs", headers=headers, json={"title": str(index), "content": "Body"})
        first = self.client.get("/blogs?limit=6").json()
        second = self.client.get("/blogs?limit=6&page=2").json()
        self.assertEqual(first["total"], 7)
        self.assertEqual(len(first["data"]), 6)
        self.assertEqual(len(second["data"]), 1)
        self.assertFalse({p["id"] for p in first["data"]} & {p["id"] for p in second["data"]})
        self.assertEqual(self.client.get("/blogs?page=99").json()["data"], [])
        for query in ("page=0", "limit=0", "limit=51", "category=MadeUp"):
            self.assertEqual(self.client.get(f"/blogs?{query}").status_code, 422)
        post_id = first["data"][0]["id"]
        updated = self.client.put(f"/blogs/{post_id}", headers=headers, json={"title": "Updated", "content": "Body", "category": "Sports"}).json()
        self.assertEqual(updated["category"], "Sports")
        unchanged = self.client.put(f"/blogs/{post_id}", headers=headers, json={"title": "Again", "content": "Body"}).json()
        self.assertEqual(unchanged["category"], "Sports")

    def test_literal_search_wildcards(self):
        self.register()
        headers = self.login()
        for title in ("100%_real", "ordinary"):
            self.client.post("/blogs", headers=headers, json={"title": title, "content": "Body"})
        result = self.client.get("/blogs", params={"search": "%_"}).json()
        self.assertEqual(result["total"], 1)
        self.assertEqual(result["data"][0]["title"], "100%_real")


if __name__ == "__main__":
    unittest.main()

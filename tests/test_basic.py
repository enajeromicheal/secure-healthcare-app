import unittest

from app import app


class BasicRouteTests(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        app.config["WTF_CSRF_ENABLED"] = False
        self.client = app.test_client()

    def test_home_page_loads(self):
        response = self.client.get("/", base_url="https://localhost")
        self.assertEqual(response.status_code, 200)

    def test_login_page_loads(self):
        response = self.client.get("/login", base_url="https://localhost")
        self.assertEqual(response.status_code, 200)

    def test_register_page_loads(self):
        response = self.client.get("/register", base_url="https://localhost")
        self.assertEqual(response.status_code, 200)

    def test_dashboard_requires_login(self):
        response = self.client.get(
            "/dashboard",
            base_url="https://localhost",
            follow_redirects=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Please log in first.", response.data)


if __name__ == "__main__":
    unittest.main()
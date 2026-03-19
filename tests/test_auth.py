import unittest

from werkzeug.security import generate_password_hash

from app import app
from db.users_mongo import create_user, delete_user


class TestAuthentication(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        app.config["WTF_CSRF_ENABLED"] = False
        self.client = app.test_client()

        self.test_username = "testpatient_auth"
        self.test_password = "TestPass123!"

        delete_user(self.test_username)

        password_hash = generate_password_hash(
            self.test_password,
            method="pbkdf2:sha256",
            salt_length=16
        )

        create_user(
            self.test_username,
            password_hash,
            role="patient",
            must_change_password=False
        )

    def tearDown(self):
        delete_user(self.test_username)

    def test_valid_login_redirects_to_dashboard(self):
        response = self.client.post(
            "/login",
            data={
                "username": self.test_username,
                "password": self.test_password,
            },
            follow_redirects=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Login successful.", response.data)
        self.assertIn(b"Dashboard", response.data)

    def test_invalid_login_shows_error(self):
        response = self.client.post(
            "/login",
            data={
                "username": self.test_username,
                "password": "WrongPassword123!",
            },
            follow_redirects=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Invalid login details.", response.data)

    def test_logout_clears_session(self):
        with self.client.session_transaction() as sess:
            sess["username"] = self.test_username
            sess["role"] = "patient"

        response = self.client.get("/logout", follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"You have been logged out.", response.data)

        with self.client.session_transaction() as sess:
            self.assertNotIn("username", sess)
            self.assertNotIn("role", sess)

    def test_dashboard_requires_login_after_logout(self):
        with self.client.session_transaction() as sess:
            sess["username"] = self.test_username
            sess["role"] = "patient"

        self.client.get("/logout", follow_redirects=True)

        response = self.client.get("/dashboard", follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Please log in first.", response.data)


if __name__ == "__main__":
    unittest.main()
import unittest

from app import app


class RBACTests(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        app.config["WTF_CSRF_ENABLED"] = False
        self.client = app.test_client()

    def login_as_role(self, username, role):
        with self.client.session_transaction() as sess:
            sess["username"] = username
            sess["role"] = role

    def test_patient_cannot_access_admin_create_patient(self):
        self.login_as_role("patient1", "patient")
        response = self.client.get("/admin/create-patient", follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Access denied", response.data)

    def test_patient_cannot_access_patients_page(self):
        self.login_as_role("patient1", "patient")
        response = self.client.get("/patients", follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Access denied", response.data)

    def test_patient_cannot_access_prescriptions_admin_view(self):
        self.login_as_role("patient1", "patient")
        response = self.client.get("/prescriptions", follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Access denied", response.data)

    def test_admin_can_access_admin_create_patient(self):
        self.login_as_role("admin1", "admin")
        response = self.client.get("/admin/create-patient")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Create Patient", response.data)

    def test_admin_can_access_patients_page(self):
        self.login_as_role("admin1", "admin")
        response = self.client.get("/patients")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Patient Records", response.data)

    def test_clinician_can_access_patients_page(self):
        self.login_as_role("clinician1", "clinician")
        response = self.client.get("/patients")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Patient Records", response.data)

    def test_clinician_can_access_prescriptions_page(self):
        self.login_as_role("clinician1", "clinician")
        response = self.client.get("/prescriptions")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Prescriptions", response.data)

    def test_clinician_cannot_access_admin_reset_password(self):
        self.login_as_role("clinician1", "clinician")
        response = self.client.get("/admin/reset-password", follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Access denied", response.data)


if __name__ == "__main__":
    unittest.main()
import os
import sys
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Force loading the .env file from the project root
load_dotenv(dotenv_path=".env")

from werkzeug.security import generate_password_hash
from db.users_mongo import create_user, ensure_user_indexes

def main():
    ensure_user_indexes()

    admin_password = generate_password_hash("Admin@123", method="pbkdf2:sha256", salt_length=16)
    patient_temp_password = generate_password_hash("TempPass@123", method="pbkdf2:sha256", salt_length=16)

    users_to_create = [
        ("admin1", admin_password, "admin", False),
        ("admin2", admin_password, "admin", False),
        ("donald", patient_temp_password, "patient", True),
        ("fatima", patient_temp_password, "patient", True),
        ("james", patient_temp_password, "patient", True),
    ]

    for username, password_hash, role, must_change_password in users_to_create:
        ok, reason = create_user(
            username=username,
            password_hash=password_hash,
            role=role,
            must_change_password=must_change_password
        )
        print(username, ok, reason)

if __name__ == "__main__":
    main()
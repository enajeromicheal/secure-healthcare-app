import os
import sys
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(override=True)

from db.users_mongo import create_user, ensure_user_indexes

load_dotenv(override=True)

if __name__ == "__main__":
    ensure_user_indexes()

    username = "clinician1"
    password = "ClinicianPass123!"
    password_hash = generate_password_hash(password, method="pbkdf2:sha256", salt_length=16)

    ok, reason = create_user(username, password_hash, role="clinician")
    print("OK:", ok, "Reason:", reason)
    print("Clinician login:", username, password)
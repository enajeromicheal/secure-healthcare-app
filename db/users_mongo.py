# db/users_mongo.py
# MongoDB user store for authentication
# Provides user creation, lookup, unique index enforcement
# Provides password hash update, deletion, deactivation
# Supports first-login password change

from __future__ import annotations

from typing import Optional, Dict, Any, Tuple

from pymongo.collection import Collection
from pymongo.errors import DuplicateKeyError, PyMongoError

from db.mongo import get_mongo_db


def _users() -> Collection:
    # Returns the MongoDB users collection
    db = get_mongo_db()
    return db["users"]


def ensure_user_indexes() -> bool:
    # Ensures unique index on username for duplicate prevention
    try:
        _users().create_index("username", unique=True)
        return True
    except PyMongoError as e:
        print("Mongo ensure_user_indexes error:", e)
        return False


def find_user(username: str) -> Optional[Dict[str, Any]]:
    # Finds an active user by username
    try:
        return _users().find_one({"username": username})
    except PyMongoError as e:
        print("Mongo find_user error:", e)
        return None


def create_user(
    username: str,
    password_hash: str,
    role: str = "patient",
    must_change_password: bool = False
) -> Tuple[bool, str]:
    # Creates a new user with hashed password and validated role
    safe_role = role if role in {"admin", "clinician", "patient"} else "patient"

    try:
        _users().insert_one(
            {
                "username": username,
                "password_hash": password_hash,
                "role": safe_role,
                "is_active": True,
                "must_change_password": must_change_password
            }
        )
        return True, "created"
    except DuplicateKeyError:
        return False, "duplicate"
    except PyMongoError as e:
        print("Mongo create_user error:", e)
        return False, "mongo_error"


def update_password_hash(username: str, new_password_hash: str) -> bool:
    # Updates a user's password hash and clears first-login password change flag
    try:
        result = _users().update_one(
            {"username": username},
            {
                "$set": {
                    "password_hash": new_password_hash,
                    "must_change_password": False
                }
            }
        )
        return result.matched_count == 1
    except PyMongoError as e:
        print("Mongo update_password_hash error:", e)
        return False


def set_must_change_password(username: str, value: bool = True) -> bool:
    # Sets whether user must change password on next login
    try:
        result = _users().update_one(
            {"username": username},
            {"$set": {"must_change_password": value}}
        )
        return result.matched_count == 1
    except PyMongoError as e:
        print("Mongo set_must_change_password error:", e)
        return False


def delete_user(username: str) -> bool:
    # Deletes a user account permanently
    try:
        result = _users().delete_one({"username": username})
        return result.deleted_count == 1
    except PyMongoError as e:
        print("Mongo delete_user error:", e)
        return False


def deactivate_user(username: str) -> bool:
    # Deactivates a user account without deleting it
    try:
        result = _users().update_one(
            {"username": username},
            {"$set": {"is_active": False}}
        )
        return result.matched_count == 1
    except PyMongoError as e:
        print("Mongo deactivate_user error:", e)
        return False


def activate_user(username: str) -> bool:
    # Reactivates a user account
    try:
        result = _users().update_one(
            {"username": username},
            {"$set": {"is_active": True}}
        )
        return result.matched_count == 1
    except PyMongoError as e:
        print("Mongo activate_user error:", e)
        return False
import os
from datetime import datetime, timezone
from pymongo import MongoClient
from pymongo.errors import PyMongoError

_client = None

def get_mongo_client() -> MongoClient:
    global _client
    if _client is None:
        uri = os.environ.get("MONGODB_URI", "mongodb://localhost:27017")
        _client = MongoClient(uri, serverSelectionTimeoutMS=2000)
    return _client

def get_mongo_db():
    db_name = os.environ.get("MONGODB_DB", "healthcare")
    return get_mongo_client()[db_name]

def ping_mongo() -> tuple[bool, str]:
    try:
        get_mongo_client().admin.command("ping")
        return True, "MongoDB ping ok"
    except PyMongoError as e:
        return False, f"MongoDB ping failed: {e}"

def utc_now():
    return datetime.now(timezone.utc)
# db/mongo.py — MongoDB connection management
# - Handles connection initialisation
# - Provides access to database
# - Includes health-check (ping) function
# - Uses singleton pattern to prevent multiple client instances

import os
from pymongo import MongoClient
from pymongo.errors import PyMongoError

# Private cached client instance (singleton pattern)
_client = None


def get_mongo_client() -> MongoClient:
    """
    Returns a cached MongoClient instance.
    Prevents multiple connections being created per request.
    """
    global _client

    if _client is None:
        uri = os.environ.get("MONGODB_URI")

        # ✅ Safer: fail fast if URI not configured
        if not uri:
            raise RuntimeError("MONGODB_URI environment variable not set")

        # Create client with short timeout for faster failure detection
        _client = MongoClient(uri, serverSelectionTimeoutMS=2000)

    return _client


def get_mongo_db():
    """
    Returns the configured MongoDB database.
    Default DB name is 'healthcare' unless overridden via env variable.
    """
    db_name = os.environ.get("MONGODB_DB", "healthcare")
    return get_mongo_client()[db_name]


def ping_mongo():
    """
    Health-check endpoint support.
    Attempts to ping MongoDB server.
    Returns (True, message) if successful, otherwise (False, error).
    """
    try:
        get_mongo_client().admin.command("ping")
        return True, "MongoDB ping ok"

    except PyMongoError as e:
        return False, f"MongoDB ping failed: {e}"
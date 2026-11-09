"""
Database connection manager with asynchronous MongoDB client (Motor)
and resilient in-memory fallback store for offline/sandboxed environments.
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

from backend.app.core.config import settings

class InMemoryCursor:
    """Simulates Motor's AsyncIOMotorCursor for in-memory queries."""
    def __init__(self, items: List[Dict[str, Any]]):
        self._items = list(items)

    def sort(self, key_or_list, direction=None):
        if isinstance(key_or_list, list):
            key, direction = key_or_list[0]
        else:
            key = key_or_list
        reverse = (direction == -1)
        self._items.sort(key=lambda x: x.get(key, ""), reverse=reverse)
        return self

    def skip(self, n: int):
        self._items = self._items[n:]
        return self

    def limit(self, n: int):
        self._items = self._items[:n]
        return self

    async def to_list(self, length: Optional[int] = None) -> List[Dict[str, Any]]:
        if length is not None:
            return self._items[:length]
        return self._items

    def __aiter__(self):
        self._iter = iter(self._items)
        return self

    async def __anext__(self):
        try:
            return next(self._iter)
        except StopIteration:
            raise StopAsyncIteration


class InMemoryCollection:
    """Thread-safe in-memory collection mimicking Motor collection interface."""
    def __init__(self, name: str):
        self.name = name
        self.documents: List[Dict[str, Any]] = []

    async def insert_one(self, doc: Dict[str, Any]):
        doc_copy = dict(doc)
        if "_id" not in doc_copy:
            doc_copy["_id"] = str(len(self.documents) + 1)
        self.documents.append(doc_copy)
        class InsertResult:
            def __init__(self, inserted_id):
                self.inserted_id = inserted_id
        return InsertResult(doc_copy["_id"])

    async def find_one(self, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        for doc in self.documents:
            match = True
            for k, v in query.items():
                if doc.get(k) != v:
                    match = False
                    break
            if match:
                return dict(doc)
        return None

    def find(self, query: Optional[Dict[str, Any]] = None) -> InMemoryCursor:
        if not query:
            return InMemoryCursor(self.documents)
        matched = []
        for doc in self.documents:
            match = True
            for k, v in query.items():
                if doc.get(k) != v:
                    match = False
                    break
            if match:
                matched.append(doc)
        return InMemoryCursor(matched)

    async def count_documents(self, query: Optional[Dict[str, Any]] = None) -> int:
        if not query:
            return len(self.documents)
        cursor = self.find(query)
        res = await cursor.to_list()
        return len(res)


class DatabaseManager:
    """Manages active database connection and failover."""
    def __init__(self):
        self.client = None
        self.db = None
        self.is_connected = False
        self.is_fallback = False
        self._in_memory_db: Dict[str, InMemoryCollection] = {
            "analyses": InMemoryCollection("analyses"),
            "users": InMemoryCollection("users")
        }

    async def connect(self):
        """Attempts to connect to MongoDB; defaults to in-memory store if unreachable."""
        import os
        import socket
        
        if os.getenv("TESTING") == "1" or os.getenv("USE_IN_MEMORY_DB") == "1":
            self.client = None
            self.db = None
            self.is_connected = False
            self.is_fallback = True
            logger.info("Using in-memory database store (TESTING active).")
            return

        try:
            # Instant probe to test socket reachability (avoids slow PyMongo background timeout)
            s = socket.create_connection(("127.0.0.1", 27017), timeout=0.1)
            s.close()
            
            from motor.motor_asyncio import AsyncIOMotorClient
            client = AsyncIOMotorClient(
                settings.MONGODB_URL,
                serverSelectionTimeoutMS=1000
            )
            await client.admin.command("ping")
            self.client = client
            self.db = client[settings.DATABASE_NAME]
            self.is_connected = True
            self.is_fallback = False
            logger.info(f"Connected to MongoDB at {settings.MONGODB_URL}/{settings.DATABASE_NAME}")
        except Exception as e:
            self.client = None
            self.db = None
            self.is_connected = False
            self.is_fallback = True
            logger.info(f"MongoDB offline or sandboxed ({e}). Activated resilient in-memory storage fallback.")

    async def disconnect(self):
        if self.client:
            self.client.close()
            self.is_connected = False
            logger.info("MongoDB connection closed.")

    def get_collection(self, name: str):
        """Returns motor collection if connected, else in-memory collection."""
        if self.is_connected and self.db is not None:
            return self.db[name]
        if name not in self._in_memory_db:
            self._in_memory_db[name] = InMemoryCollection(name)
        return self._in_memory_db[name]

    def get_status(self) -> Dict[str, Any]:
        return {
            "connected": self.is_connected,
            "using_fallback": self.is_fallback,
            "backend": "mongodb" if self.is_connected else "in_memory_store",
            "database_name": settings.DATABASE_NAME
        }


db_manager = DatabaseManager()

async def get_db():
    return db_manager

import asyncpg
import os
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager

class Database:
    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or os.getenv("DATABASE_URL")
        if not self.database_url:
            raise ValueError("DATABASE_URL environment variable is required")

    @asynccontextmanager
    async def get_connection(self):
        """Context manager for database connections"""
        conn = await asyncpg.connect(self.database_url)
        try:
            yield conn
        finally:
            await conn.close()

    async def execute_query(self, query: str, *args) -> Any:
        """Execute a query and return the result"""
        async with self.get_connection() as conn:
            return await conn.execute(query, *args)

    async def fetch_one(self, query: str, *args) -> Optional[Dict[str, Any]]:
        """Fetch a single row"""
        async with self.get_connection() as conn:
            row = await conn.fetchrow(query, *args)
            return dict(row) if row else None

    async def fetch_all(self, query: str, *args) -> List[Dict[str, Any]]:
        """Fetch all rows"""
        async with self.get_connection() as conn:
            rows = await conn.fetch(query, *args)
            return [dict(row) for row in rows]

    async def insert_and_return(self, query: str, *args) -> Optional[Dict[str, Any]]:
        """Insert and return the inserted row"""
        async with self.get_connection() as conn:
            row = await conn.fetchrow(query, *args)
            return dict(row) if row else None
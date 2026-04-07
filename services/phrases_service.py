from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from database import Database

class PhraseIn(BaseModel):
    phrase: str
    translation: str
    updated_by: str

class PhraseService:
    def __init__(self, db: Database):
        self.db = db

    async def create_phrase(self, data: PhraseIn) -> Optional[Dict[str, Any]]:
        query = """
            INSERT INTO phrases (phrase, translation, updated_by)
            VALUES ($1, $2, $3)
            RETURNING id, phrase, translation, updated_at, updated_by
        """
        return await self.db.insert_and_return(query, data.phrase, data.translation, data.updated_by)

    async def get_all_phrases(self) -> List[Dict[str, Any]]:
        query = "SELECT * FROM phrases ORDER BY id"
        return await self.db.fetch_all(query)

    async def get_phrase_by_id(self, phrase_id: int) -> Optional[Dict[str, Any]]:
        query = "SELECT * FROM phrases WHERE id = $1"
        return await self.db.fetch_one(query, phrase_id)

    async def update_phrase(self, phrase_id: int, data: PhraseIn) -> Optional[Dict[str, Any]]:
        query = """
            UPDATE phrases
            SET phrase = $1, translation = $2, updated_by = $3, updated_at = NOW()
            WHERE id = $4
            RETURNING id, phrase, translation, updated_at, updated_by
        """
        return await self.db.insert_and_return(query, data.phrase, data.translation, data.updated_by, phrase_id)

    async def delete_phrase(self, phrase_id: int) -> bool:
        query = "DELETE FROM phrases WHERE id = $1"
        return await self.db.execute_query(query, phrase_id)
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
import asyncpg
import os

app = FastAPI()

DATABASE_URL = os.getenv("DATABASE_URL")

async def get_db():
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        yield conn
    finally:
        await conn.close()

# Pydantic model for input validation
class PhraseIn(BaseModel):
    phrase: str
    translation: str
    updated_by: str

# Create
@app.post("/phrases")
async def create_phrase(data: PhraseIn, db=Depends(get_db)):
    query = """
        INSERT INTO phrases (phrase, translation, updated_by)
        VALUES ($1, $2, $3)
        RETURNING id, phrase, translation, updated_at, updated_by
    """
    row = await db.fetchrow(query, data.phrase, data.translation, data.updated_by)
    return dict(row)

# Read all
@app.get("/phrases")
async def list_phrases(db=Depends(get_db)):
    rows = await db.fetch("SELECT * FROM phrases ORDER BY id")
    return [dict(r) for r in rows]

# Read one
@app.get("/phrases/{id}")
async def get_phrase(id: int, db=Depends(get_db)):
    row = await db.fetchrow("SELECT * FROM phrases WHERE id=$1", id)
    if not row:
        raise HTTPException(status_code=404, detail="Phrase not found")
    return dict(row)

# Update
@app.put("/phrases/{id}")
async def update_phrase(id: int, data: PhraseIn, db=Depends(get_db)):
    query = """
        UPDATE phrases
        SET phrase=$1, translation=$2, updated_by=$3, updated_at=NOW()
        WHERE id=$4
        RETURNING id, phrase, translation, updated_at, updated_by
    """
    row = await db.fetchrow(query, data.phrase, data.translation, data.updated_by, id)
    if not row:
        raise HTTPException(status_code=404, detail="Phrase not found")
    return dict(row)

# Delete
@app.delete("/phrases/{id}")
async def delete_phrase(id: int, db=Depends(get_db)):
    result = await db.execute("DELETE FROM phrases WHERE id=$1", id)
    if result == "DELETE 0":
        raise HTTPException(status_code=404, detail="Phrase not found")
    return {"status": "deleted", "id": id}

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from uuid import uuid4


class ItemCreate(BaseModel):
    name: str
    description: Optional[str] = None


class Item(ItemCreate):
    id: str


app = FastAPI(title="Simple Items API")

# In-memory store: dict[id, Item]
db: dict[str, Item] = {}


@app.post("/items", response_model=Item)
def create_item(item: ItemCreate):
    item_id = str(uuid4())
    new = Item(id=item_id, **item.dict())
    db[item_id] = new
    return new


@app.get("/items/{item_id}", response_model=Item)
def read_item(item_id: str):
    item = db.get(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@app.get("/items", response_model=List[Item])
def list_items():
    return list(db.values())


@app.put("/items/{item_id}", response_model=Item)
def update_item(item_id: str, payload: ItemCreate):
    existing = db.get(item_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Item not found")
    updated = Item(id=item_id, **payload.dict())
    db[item_id] = updated
    return updated


@app.delete("/items/{item_id}")
def delete_item(item_id: str):
    if item_id not in db:
        raise HTTPException(status_code=404, detail="Item not found")
    del db[item_id]
    return {"ok": True}

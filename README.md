# Simple FastAPI example

This project contains a minimal FastAPI application with Pydantic models and in-memory storage.

Run locally:

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 9999
```

Endpoints:
- POST /items — create item (body: {"name": "...", "description": "..."})
- GET /items — list items
- GET /items/{id} — get item
- PUT /items/{id} — update item
- DELETE /items/{id} — delete item

Open interactive docs at http://127.0.0.1:9999/docs

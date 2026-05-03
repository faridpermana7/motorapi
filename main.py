from asyncpg import transaction
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import auth
from core.database_sqlalchemy import create_tables
from dotenv import load_dotenv

from routers.admin import logins, menus, phrases, users
from routers.master import customers, enum_tables, items, locations, weather
from routers.transaction import cashier_logs, transaction_items, transactions

# Load environment variables from .env file
load_dotenv()

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://127.0.0.1",
        "http://127.0.0.1:8000",
        "http://127.0.0.1:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["authentication"])

# Admin
app.include_router(logins.router)
app.include_router(phrases.router)
app.include_router(users.router)
app.include_router(menus.router)

# Master
app.include_router(weather.router)
app.include_router(locations.router)
app.include_router(enum_tables.router)
app.include_router(items.router)
app.include_router(customers.router)

# Transaction
app.include_router(transactions.router)
app.include_router(transaction_items.router)
app.include_router(cashier_logs.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9999)

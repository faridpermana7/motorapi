from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import logins, phrases, users, weather, locations
from database_sqlalchemy import create_tables
from dotenv import load_dotenv

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
app.include_router(phrases.router)
app.include_router(users.router)
app.include_router(weather.router)
app.include_router(locations.router)
app.include_router(logins.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9999)

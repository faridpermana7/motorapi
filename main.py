from asyncpg import transaction
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY

from routers import auth 
from dotenv import load_dotenv 
from routers.admin import configurations, logins, menus, phrases, users
from routers.master import customers, enum_tables, items, locations, weather
from routers.transaction import cashier_logs, transaction_items, transactions

# Load environment variables from .env file
load_dotenv()

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:8080",
        "http://127.0.0.1:10000",
        "http://motor.web:10000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc: RequestValidationError):
    errors = []
    for err in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in err["loc"]),
            "message": err["msg"],
            "type": err["type"]
        })
    return JSONResponse(
        status_code=HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": errors}
    )

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["authentication"])

# Admin
app.include_router(logins.router)
app.include_router(phrases.router)
app.include_router(users.router)
app.include_router(menus.router)
app.include_router(configurations.router)

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

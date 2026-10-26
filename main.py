from asyncpg import transaction
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY

from routers import auth 
from dotenv import load_dotenv 
from routers.admin import configurations, logins, menus, phrases, roles, users
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
        "https://127.0.0.1:8080",

        "http://localhost:8081",
        "https://localhost:8081",

        "https://motor.web:8080",
        "https://motor.web:8081",
        "https://motor.web:10000",
        "https://motor.web:10001",
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
app.include_router(logins.router, prefix="/logins", tags=["logins"])
app.include_router(phrases.router, prefix="/phrases", tags=["phrases"])
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(menus.router, prefix="/menus", tags=["menus"])
app.include_router(configurations.router, prefix="/configurations", tags=["configurations"])
app.include_router(roles.router, prefix="/roles", tags=["roles"])

# Master
app.include_router(weather.router, prefix="/weather", tags=["weather"])
app.include_router(locations.router, prefix="/locations", tags=["locations"])
app.include_router(enum_tables.router, prefix="/enum_tables", tags=["enum-tables"])
app.include_router(items.router, prefix="/items", tags=["items"])
app.include_router(customers.router, prefix="/customers", tags=["customers"])

# Transaction
app.include_router(transactions.router, prefix="/transactions", tags=["transactions"])
app.include_router(transaction_items.router, prefix="/transaction_items", tags=["transaction-items"])
app.include_router(cashier_logs.router, prefix="/cashier_logs", tags=["cashier-logs"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9999, log_config="log_config.json")

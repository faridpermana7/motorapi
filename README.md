# MotorAPI - FastAPI Application with OAuth2 JWT Authentication

This project contains a FastAPI application with SQLAlchemy ORM, Pydantic models, and OAuth2 JWT authentication.

## Setup

Run locally:

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --host 127.0.0.1 --port 9999
```

## Authentication

The API uses OAuth2 with JWT tokens for authentication.

### Login
```http
POST /auth/login
Content-Type: application/x-www-form-urlencoded

username=testuser&password=testpass
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### Using Protected Endpoints
Include the token in the Authorization header:
```
Authorization: Bearer <access_token>
```

### Token Expiration
- Tokens expire after 30 minutes
- Users must re-login after expiration
- The `/auth/me` endpoint returns current user information

## API Endpoints

### Authentication
- `POST /auth/login` — Login with username/password
- `GET /auth/me` — Get current user info (requires authentication)

### Users
- `POST /users` — Create user
- `GET /users` — List users (requires authentication)
- `GET /users/{id}` — Get user (requires authentication)
- `PUT /users/{id}` — Update user (requires authentication)
- `DELETE /users/{id}` — Delete user (requires authentication)

### Other Endpoints
- Logins, Phrases, Weather, Locations (see router files for details)

## Testing Authentication

Run the test script:
```bash
python test_auth.py
```

## Security Notes
- Change the `SECRET_KEY` in `services/auth_service.py` for production
- Store the secret key in environment variables
- Passwords are hashed using bcrypt
- JWT tokens include user ID and username
- Token expiration enforces re-login after 30 minutes

Open interactive docs at http://127.0.0.1:9999/docs

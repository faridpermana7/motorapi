# MotorAPI - FastAPI Application with OAuth2 JWT Authentication

This project contains a FastAPI application with SQLAlchemy ORM, Pydantic models, and OAuth2 JWT authentication.

## Setup

Run locally:

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn main:app --host 127.0.0.1 --port 9999 --log-config log_config.json
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

Paged responses use the reusable `PaginationResponseDTO[RecordDTO]` model, so endpoints can paginate item, transaction, enum, or other response DTOs without defining a separate pagination model for each entity.

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


## Testing Authentication
running as server by task schedule manager with run_server.bat


## Running as Service NSSM

### configure the user local first
Step 1: Grant "Log on as a service" RightsMethod A: Using Local Security Policy (Windows Pro / Enterprise)
1. Press Win + R, type secpol.msc, and press Enter.
2. In the left panel, navigate to:Local Policies $\rightarrow$ User Rights Assignment.
3. In the right panel, double-click Log on as a service.
4. Click Add User or Group....
5. Type your local username (e.g., pfar or farid.permana@outlook.com) into the box and click Check Names.   
6. Click OK, then Apply, and close the window.

### register the service
Open an Administrator Command Prompt (cmd) and install the service:

DOS
C:\tools\nssm.exe install MotorApiService
In the NSSM configuration window, fill out these fields:

Path: cmd.exe

Startup directory: D:\project\motorapi

Arguments: /c run_server.bat

Crucial (Logon Tab): Because this service needs to control VirtualBox, go to the Logon tab, select This account, and enter your actual Windows Username and Password (otherwise the service cannot access VirtualBox VMs tied to your profile).

Leave the NSSM I/O Tab's Stdout and Stderr paths empty. Uvicorn writes logs to `logs\server.log` with a timestamp and severity level (`INFO`, `WARNING`, `ERROR`, etc.), creating a new dated log file at midnight (for example, `server.log.2026-10-25`).

Click Install service.

Managing Your Unified Service
To Start/Stop: Open services.msc, find MotorApiService, and start it. The startup script checks whether the database VM is already running and starts it only if it is off, then clears port 9999 and launches the API. Restarting the API service does not reboot a running VM. Daily logs are stored and rotated in `D:\project\motorapi\logs`.

To remove any old separate database service you made earlier: Run nssm remove FarbuntuDatabaseService confirm in your terminal to keep your system clean.
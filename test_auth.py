#!/usr/bin/env python3
"""
Test script for OAuth2 JWT Authentication

This script demonstrates how to:
1. Register a user (if needed)
2. Login with username/password to get JWT token
3. Use the token to access protected endpoints
4. Handle token expiration

Run this script after starting the FastAPI server.
"""

import requests
import json
from datetime import datetime, timedelta

# Server configuration
BASE_URL = "http://127.0.0.1:9999"

def test_login():
    """Test the login endpoint to get JWT token."""
    print("Testing login...")

    # Login credentials
    login_data = {
        "username": "testuser",  # Change this to an existing user
        "password": "testpass"   # Change this to the correct password
    }

    response = requests.post(f"{BASE_URL}/auth/login", data=login_data)

    if response.status_code == 200:
        token_data = response.json()
        print("Login successful!")
        print(f"Access Token: {token_data['access_token']}")
        print(f"Token Type: {token_data['token_type']}")
        return token_data['access_token']
    else:
        print(f"Login failed: {response.status_code}")
        print(response.text)
        return None

def test_protected_endpoint(token):
    """Test accessing a protected endpoint with JWT token."""
    print("\nTesting protected endpoint...")

    headers = {
        "Authorization": f"Bearer {token}"
    }

    response = requests.get(f"{BASE_URL}/auth/me", headers=headers)

    if response.status_code == 200:
        user_data = response.json()
        print("Protected endpoint accessed successfully!")
        print(f"User: {user_data['username']} (ID: {user_data['id']})")
    else:
        print(f"Protected endpoint failed: {response.status_code}")
        print(response.text)

def test_expired_token():
    """Demonstrate what happens with an expired token."""
    print("\nTesting expired token behavior...")

    # Create an expired token manually (this would normally be done by the server)
    # In a real scenario, wait for the token to expire or modify the token

    print("Note: Tokens expire after 30 minutes by default.")
    print("To test expiration, wait 30+ minutes after login or modify the token manually.")

def test_protected_users_endpoint(token):
    """Test accessing protected users endpoint."""
    print("\nTesting protected users endpoint...")

    headers = {
        "Authorization": f"Bearer {token}"
    }

    response = requests.get(f"{BASE_URL}/users", headers=headers)

    if response.status_code == 200:
        users = response.json()
        print("Users endpoint accessed successfully!")
        print(f"Found {len(users)} users")
    else:
        print(f"Users endpoint failed: {response.status_code}")
        print(response.text)

def main():
    """Main test function."""
    print("OAuth2 JWT Authentication Test")
    print("=" * 40)

    # Test login
    token = test_login()

    if token:
        # Test protected endpoints
        test_protected_endpoint(token)
        test_protected_users_endpoint(token)

        # Test token expiration (informational)
        test_expired_token()

        print("\n" + "=" * 40)
        print("Test completed!")
        print("\nTo use the API:")
        print("1. Login at POST /auth/login with username/password")
        print("2. Use the returned token in Authorization header: 'Bearer <token>'")
        print("3. Token expires in 30 minutes, requiring re-login")
    else:
        print("Login failed. Make sure you have a user in the database.")
        print("You can create a user via POST /users endpoint first.")

if __name__ == "__main__":
    main()
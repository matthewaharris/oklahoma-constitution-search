#!/usr/bin/env python3
"""
Authentication helpers for verifying Clerk JWT tokens
"""

import os
import requests
from functools import wraps
from flask import request, jsonify
from typing import Optional, Dict
from jose import jwt, JWTError
from jose.exceptions import JWKError

# Import configurations
if os.getenv('PRODUCTION') or os.getenv('RENDER'):
    from config_production import CLERK_SECRET_KEY, CLERK_FRONTEND_API
else:
    try:
        from config import CLERK_SECRET_KEY, CLERK_FRONTEND_API
    except ImportError:
        from config_production import CLERK_SECRET_KEY, CLERK_FRONTEND_API


# Cache for JWKS (JSON Web Key Set)
_jwks_cache = None


def get_clerk_jwks():
    """Fetch Clerk's JSON Web Key Set (JWKS) for JWT verification"""
    global _jwks_cache

    # Return cached version if available
    if _jwks_cache:
        return _jwks_cache

    try:
        jwks_url = f"{CLERK_FRONTEND_API}/.well-known/jwks.json"
        response = requests.get(jwks_url, timeout=5)
        response.raise_for_status()
        _jwks_cache = response.json()
        return _jwks_cache
    except Exception as e:
        print(f"[ERROR] Failed to fetch Clerk JWKS: {e}")
        return None


def verify_clerk_token(token: str) -> Optional[Dict]:
    """
    Verify a Clerk JWT token and return the decoded payload

    Args:
        token: JWT token from Authorization header

    Returns:
        Decoded token payload if valid, None otherwise
    """
    if not token:
        return None

    try:
        # Remove 'Bearer ' prefix if present
        if token.startswith('Bearer '):
            token = token[7:]

        # Get JWKS from Clerk
        jwks = get_clerk_jwks()
        if not jwks:
            print("[ERROR] Could not get Clerk JWKS")
            return None

        # Decode the token header to get the key ID (kid)
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get('kid')

        if not kid:
            print("[ERROR] No 'kid' in token header")
            return None

        # Find the matching key in JWKS
        key = None
        for jwk in jwks.get('keys', []):
            if jwk.get('kid') == kid:
                key = jwk
                break

        if not key:
            print(f"[ERROR] No matching key found for kid: {kid}")
            return None

        # Verify and decode the JWT
        try:
            decoded = jwt.decode(
                token,
                key,
                algorithms=['RS256'],
                options={"verify_aud": False}  # Clerk doesn't use 'aud' claim
            )
            return decoded
        except JWTError as e:
            print(f"[ERROR] JWT verification failed: {e}")
            return None

    except Exception as e:
        print(f"[ERROR] Token verification failed: {e}")
        return None


def get_user_from_request() -> Optional[Dict]:
    """
    Extract and verify user from Authorization header

    Returns:
        User info dict if authenticated, None if anonymous
    """
    auth_header = request.headers.get('Authorization')

    if not auth_header:
        return None  # Anonymous user - this is OK

    token_payload = verify_clerk_token(auth_header)

    if not token_payload:
        return None  # Invalid token - treat as anonymous

    # Extract user information from Clerk JWT payload
    return {
        'user_id': token_payload.get('sub'),  # Clerk user ID
        'email': token_payload.get('email'),
        'email_verified': token_payload.get('email_verified', False),
        'first_name': token_payload.get('first_name'),
        'last_name': token_payload.get('last_name'),
        'full_name': token_payload.get('name'),
        'image_url': token_payload.get('image_url')
    }


def optional_auth(f):
    """
    Decorator for routes that support optional authentication
    Adds 'current_user' to kwargs (None if anonymous)
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_user_from_request()
        kwargs['current_user'] = user
        return f(*args, **kwargs)
    return decorated_function


def require_auth(f):
    """
    Decorator for routes that require authentication
    Returns 401 if not authenticated
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_user_from_request()

        if not user:
            return jsonify({'error': 'Authentication required'}), 401

        kwargs['current_user'] = user
        return f(*args, **kwargs)
    return decorated_function


if __name__ == "__main__":
    # Test the authentication helpers
    print("Testing Clerk authentication helpers...")

    # Test JWKS fetch
    jwks = get_clerk_jwks()
    if jwks:
        print(f"[OK] Successfully fetched JWKS with {len(jwks.get('keys', []))} keys")
    else:
        print("[ERROR] Failed to fetch JWKS")

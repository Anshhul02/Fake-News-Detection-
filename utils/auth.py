"""
============================================================
AUTHENTICATION UTILITIES
============================================================

Handles:

- Argon2 password hashing
- Password verification
- JWT access-token creation
- JWT token decoding
- Current-user authentication
- Admin authentication
============================================================
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from jose import JWTError, jwt

from argon2 import PasswordHasher
from argon2.exceptions import (
    VerifyMismatchError,
    VerificationError,
)

from backend.config import settings


# ============================================================
# CONFIGURATION
# ============================================================

JWT_ALGORITHM = "HS256"

ACCESS_TOKEN_EXPIRE_MINUTES = 60


# ============================================================
# ARGON2 PASSWORD HASHER
# ============================================================

password_hasher = PasswordHasher(
    time_cost=3,
    memory_cost=65536,
    parallelism=4,
    hash_len=32,
    salt_len=16,
)


# ============================================================
# HASH PASSWORD
# ============================================================

def hash_password(
    password: str
) -> str:
    """
    Hash a password using Argon2id.
    """

    if not isinstance(
        password,
        str
    ):

        raise ValueError(
            "Password must be a string."
        )

    if not password:

        raise ValueError(
            "Password cannot be empty."
        )

    return password_hasher.hash(
        password
    )


# ============================================================
# VERIFY PASSWORD
# ============================================================

def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    """
    Verify a plain-text password
    against an Argon2 password hash.
    """

    if (
        not plain_password
        or not hashed_password
    ):

        return False

    try:

        return password_hasher.verify(
            hashed_password,
            plain_password,
        )

    except (
        VerifyMismatchError,
        VerificationError,
        ValueError,
    ):

        return False


# ============================================================
# OAUTH2
# ============================================================

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/auth/login"
)


# ============================================================
# JWT SECRET
# ============================================================

def get_jwt_secret_key() -> str:
    """
    Get JWT secret from application settings.
    """

    secret_key = settings.jwt_secret_key

    if not secret_key:

        raise RuntimeError(
            "JWT secret key is not configured."
        )

    return secret_key


# ============================================================
# CREATE ACCESS TOKEN
# ============================================================

def create_access_token(
    data: dict,
    expires_delta: Optional[
        timedelta
    ] = None,
) -> str:
    """
    Create a JWT access token.
    """

    to_encode = data.copy()

    if expires_delta:

        expire = (
            datetime.now(timezone.utc)
            + expires_delta
        )

    else:

        expire = (
            datetime.now(timezone.utc)
            + timedelta(
                minutes=ACCESS_TOKEN_EXPIRE_MINUTES
            )
        )

    now = datetime.now(
        timezone.utc
    )

    to_encode.update(
        {
            "exp": expire,
            "iat": now,
        }
    )

    return jwt.encode(
        to_encode,
        get_jwt_secret_key(),
        algorithm=JWT_ALGORITHM,
    )


# ============================================================
# DECODE ACCESS TOKEN
# ============================================================

def decode_access_token(
    token: str,
) -> dict:
    """
    Decode and validate a JWT token.
    """

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={
            "WWW-Authenticate": "Bearer"
        },
    )

    try:

        payload = jwt.decode(
            token,
            get_jwt_secret_key(),
            algorithms=[
                JWT_ALGORITHM
            ],
        )

        return payload

    except JWTError:

        raise credentials_exception


# ============================================================
# CURRENT USER
# ============================================================

async def get_current_user(
    token: str = Depends(
        oauth2_scheme
    ),
):
    """
    Get authenticated user information
    from the JWT token.
    """

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={
            "WWW-Authenticate": "Bearer"
        },
    )

    try:

        payload = jwt.decode(
            token,
            get_jwt_secret_key(),
            algorithms=[
                JWT_ALGORITHM
            ],
        )

        user_id = payload.get(
            "sub"
        )

        if not user_id:

            raise credentials_exception

        return {
            "id": user_id,

            "user_id": user_id,

            "name": payload.get(
                "name",
                ""
            ),

            "email": payload.get(
                "email",
                ""
            ),

            "role": payload.get(
                "role",
                "user"
            ),

            "created_at": payload.get(
                "created_at"
            ),
        }

    except JWTError:

        raise credentials_exception


# ============================================================
# CURRENT ADMIN
# ============================================================

async def get_current_admin(
    current_user: dict = Depends(
        get_current_user
    ),
):
    """
    Allow access only to users whose
    JWT role is admin.
    """

    if current_user.get(
        "role"
    ) != "admin":

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required.",
        )

    return current_user
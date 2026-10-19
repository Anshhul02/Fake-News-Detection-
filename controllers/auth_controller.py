
"""
============================================================
AUTHENTICATION CONTROLLER
============================================================

Handles:

- User registration
- User login
- Password hashing with Argon2
- Password verification
- JWT access-token generation
============================================================
"""

from datetime import datetime

from fastapi import HTTPException, status
from pymongo.errors import DuplicateKeyError

from backend.utils.auth import (
    hash_password,
    verify_password,
    create_access_token,
)

from backend.models.user_model import (
    UserRegister,
    UserLogin,
    create_user_document,
)

from backend.database import users_collection


# ============================================================
# REGISTER USER
# ============================================================

async def register_user(
    user_data: UserRegister,
):
    """
    Register a new normal user.
    """

    # --------------------------------------------------------
    # Extract data
    # --------------------------------------------------------

    name = user_data.name.strip()
    email = user_data.email.strip().lower()
    password = user_data.password

    # --------------------------------------------------------
    # Basic validation
    # --------------------------------------------------------

    if not name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Name is required.",
        )

    if len(name) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Name must contain at least 2 characters.",
        )

    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is required.",
        )

    if not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password is required.",
        )

    if len(password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must contain at least 6 characters.",
        )

    # --------------------------------------------------------
    # Check existing user
    # --------------------------------------------------------

    existing_user = await users_collection.find_one(
        {
            "email": email
        }
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    # --------------------------------------------------------
    # Hash password
    # --------------------------------------------------------

    password_hash = hash_password(
        password
    )

    # --------------------------------------------------------
    # Create database document
    # --------------------------------------------------------

    user_document = create_user_document(
        name=name,
        email=email,
        password_hash=password_hash,
        role="user",
    )

    # --------------------------------------------------------
    # Insert user
    # --------------------------------------------------------

    try:

        result = await users_collection.insert_one(
            user_document
        )

    except DuplicateKeyError:

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    # --------------------------------------------------------
    # Verify insertion
    # --------------------------------------------------------

    if not result.inserted_id:

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User registration failed.",
        )

    # --------------------------------------------------------
    # User ID
    # --------------------------------------------------------

    user_id = str(
        result.inserted_id
    )

    # --------------------------------------------------------
    # Created timestamp
    # --------------------------------------------------------

    created_at = user_document[
        "created_at"
    ]

    # --------------------------------------------------------
    # Create JWT
    # --------------------------------------------------------

    access_token = create_access_token(
        {
            "sub": user_id,
            "id": user_id,
            "name": name,
            "email": email,
            "role": "user",
            "created_at": created_at.isoformat(),
        }
    )

    # --------------------------------------------------------
    # Response
    # --------------------------------------------------------

    return {
        "success": True,

        "message": "Registration successful.",

        "token": access_token,

        "access_token": access_token,

        "token_type": "bearer",

        "user": {
            "id": user_id,
            "name": name,
            "email": email,
            "role": "user",
            "created_at": created_at,
        },
    }


# ============================================================
# LOGIN USER
# ============================================================

async def login_user(
    user_data: UserLogin,
):
    """
    Authenticate an existing user.
    """

    # --------------------------------------------------------
    # Extract data
    # --------------------------------------------------------

    email = user_data.email.strip().lower()
    password = user_data.password

    # --------------------------------------------------------
    # Basic validation
    # --------------------------------------------------------

    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is required.",
        )

    if not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password is required.",
        )

    # --------------------------------------------------------
    # Find user
    # --------------------------------------------------------

    user = await users_collection.find_one(
        {
            "email": email
        }
    )

    if not user:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    # --------------------------------------------------------
    # Get password hash
    #
    # New users:
    #     password_hash
    #
    # Existing admin:
    #     password
    # --------------------------------------------------------

    stored_password = (
        user.get("password_hash")
        or user.get("password")
    )

    if not stored_password:

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User password is not configured correctly.",
        )

    # --------------------------------------------------------
    # Verify password
    # --------------------------------------------------------

    password_valid = verify_password(
        password,
        stored_password,
    )

    if not password_valid:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    # --------------------------------------------------------
    # User information
    # --------------------------------------------------------

    user_id = str(
        user["_id"]
    )

    role = user.get(
        "role",
        "user"
    )

    name = user.get(
        "name",
        ""
    )

    stored_email = user.get(
        "email",
        email
    )

    created_at = user.get(
        "created_at"
    )

    # --------------------------------------------------------
    # JWT payload
    # --------------------------------------------------------

    token_payload = {
        "sub": user_id,
        "id": user_id,
        "name": name,
        "email": stored_email,
        "role": role,
    }

    if created_at:

        if isinstance(
            created_at,
            datetime
        ):

            token_payload[
                "created_at"
            ] = created_at.isoformat()

        else:

            token_payload[
                "created_at"
            ] = str(created_at)

    # --------------------------------------------------------
    # Create JWT
    # --------------------------------------------------------

    access_token = create_access_token(
        token_payload
    )

    # --------------------------------------------------------
    # Response
    # --------------------------------------------------------

    return {
        "success": True,

        "message": "Login successful.",

        "token": access_token,

        "access_token": access_token,

        "token_type": "bearer",

        "user": {
            "id": user_id,
            "name": name,
            "email": stored_email,
            "role": role,
            "created_at": created_at,
        },
    }


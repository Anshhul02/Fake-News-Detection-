from datetime import datetime, timezone

from pydantic import BaseModel, EmailStr, Field


# ============================================================
# REGISTER USER
# ============================================================

class UserRegister(BaseModel):

    name: str = Field(
        ...,
        min_length=2,
        max_length=100
    )

    email: EmailStr

    password: str = Field(
        ...,
        min_length=6,
        max_length=128
    )


# ============================================================
# LOGIN USER
# ============================================================

class UserLogin(BaseModel):

    email: EmailStr

    password: str = Field(
        ...,
        min_length=6,
        max_length=128
    )


# ============================================================
# USER RESPONSE
# ============================================================

class UserResponse(BaseModel):

    id: str

    name: str

    email: EmailStr

    role: str = "user"

    created_at: datetime


# ============================================================
# DATABASE USER DOCUMENT
# ============================================================

def create_user_document(
    name: str,
    email: str,
    password_hash: str,
    role: str = "user"
):

    return {
        "name": name.strip(),

        "email": email.lower().strip(),

        "password_hash": password_hash,

        "role": role,

        "created_at": datetime.now(
            timezone.utc
        )
    }
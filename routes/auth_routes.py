from fastapi import APIRouter, Depends

from backend.controllers.auth_controller import (
    login_user,
    register_user,
)

from backend.models.user_model import (
    UserLogin,
    UserRegister,
)

from backend.utils.auth import (
    get_current_user,
    get_current_admin,
)


# ============================================================
# AUTHENTICATION ROUTER
# ============================================================

router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"],
)


# ============================================================
# REGISTER
# ============================================================

@router.post("/register")
async def register(
    user_data: UserRegister,
):
    return await register_user(
        user_data
    )


# ============================================================
# LOGIN
# ============================================================

@router.post("/login")
async def login(
    user_data: UserLogin,
):
    return await login_user(
        user_data
    )


# ============================================================
# CURRENT USER
# ============================================================

@router.get("/me")
async def current_user(
    user: dict = Depends(
        get_current_user
    ),
):
    return {
        "success": True,

        "user": {
            "id": user.get(
                "id"
            ),

            "name": user.get(
                "name",
                "",
            ),

            "email": user.get(
                "email",
                "",
            ),

            "role": user.get(
                "role",
                "user",
            ),

            "created_at": user.get(
                "created_at"
            ),
        },
    }


# ============================================================
# ADMIN AUTHENTICATION TEST
# ============================================================

@router.get("/admin-test")
async def admin_test(
    admin: dict = Depends(
        get_current_admin
    ),
):
    return {
        "success": True,

        "message": "Admin authentication successful.",

        "admin": {
            "id": admin.get(
                "id"
            ),

            "name": admin.get(
                "name",
                "",
            ),

            "email": admin.get(
                "email",
                "",
            ),

            "role": admin.get(
                "role",
                "admin",
            ),
        },
    }
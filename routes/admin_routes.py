"""
============================================================
ADMIN ROUTES
============================================================

Admin-only API endpoints.

Routes:

GET /api/admin/dashboard
GET /api/admin/users/stats
GET /api/admin/users
GET /api/admin/predictions/stats
GET /api/admin/predictions/recent
============================================================
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query

from backend.controllers.admin_controller import (
    get_dashboard_stats,
    get_user_stats,
    get_all_users,
    get_prediction_stats,
    get_recent_predictions,
)

from backend.utils.auth import (
    get_current_admin,
)


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/api/admin",
    tags=["Admin"],
)


# ============================================================
# DASHBOARD
# ============================================================

@router.get("/dashboard")
async def dashboard(
    admin: dict = Depends(
        get_current_admin
    ),
):

    return await get_dashboard_stats(
        admin
    )


# ============================================================
# USER STATISTICS
# ============================================================

@router.get("/users/stats")
async def user_stats(
    admin: dict = Depends(
        get_current_admin
    ),
):

    return await get_user_stats(
        admin
    )


# ============================================================
# ALL USERS
# ============================================================

@router.get("/users")
async def users(
    limit: int = Query(
        default=100,
        ge=1,
        le=500,
    ),
    admin: dict = Depends(
        get_current_admin
    ),
):

    return await get_all_users(
        admin=admin,
        limit=limit,
    )


# ============================================================
# PREDICTION STATISTICS
# ============================================================

@router.get("/predictions/stats")
async def prediction_stats(
    admin: dict = Depends(
        get_current_admin
    ),
):

    return await get_prediction_stats(
        admin
    )


# ============================================================
# RECENT PREDICTIONS
# ============================================================

@router.get("/predictions/recent")
async def recent_predictions(
    limit: int = Query(
        default=10,
        ge=1,
        le=50,
    ),
    admin: dict = Depends(
        get_current_admin
    ),
):

    return await get_recent_predictions(
        admin=admin,
        limit=limit,
    )
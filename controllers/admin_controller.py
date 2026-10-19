"""
============================================================
ADMIN CONTROLLER
============================================================

Handles admin-only operations:

- Dashboard statistics
- User statistics
- Complete user list
- Prediction statistics
- Recent predictions
============================================================
"""

from fastapi import HTTPException, status

from backend.database import (
    users_collection,
    predictions_collection,
)


# ============================================================
# ADMIN AUTHORIZATION
# ============================================================

def verify_admin(admin: dict):

    if not admin:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
        )

    if admin.get("role") != "admin":

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required.",
        )

    return admin


# ============================================================
# DASHBOARD STATISTICS
# ============================================================

async def get_dashboard_stats(
    admin: dict,
):

    verify_admin(admin)

    total_users = await users_collection.count_documents({})

    total_admins = await users_collection.count_documents({
        "role": "admin"
    })

    normal_users = await users_collection.count_documents({
        "role": "user"
    })

    total_predictions = (
        await predictions_collection.count_documents({})
    )

    fake_predictions = (
        await predictions_collection.count_documents({
            "label": "FAKE"
        })
    )

    real_predictions = (
        await predictions_collection.count_documents({
            "label": "REAL"
        })
    )

    return {
        "success": True,

        "statistics": {

            "users": {
                "total": total_users,
                "normal_users": normal_users,
                "admins": total_admins,
            },

            "predictions": {
                "total": total_predictions,
                "fake": fake_predictions,
                "real": real_predictions,
            },
        },
    }


# ============================================================
# USER STATISTICS
# ============================================================

async def get_user_stats(
    admin: dict,
):

    verify_admin(admin)

    total_users = await users_collection.count_documents({})

    normal_users = await users_collection.count_documents({
        "role": "user"
    })

    admins = await users_collection.count_documents({
        "role": "admin"
    })

    return {
        "success": True,

        "users": {
            "total": total_users,
            "normal_users": normal_users,
            "admins": admins,
        },
    }


# ============================================================
# GET ALL USERS
# ============================================================

async def get_all_users(
    admin: dict,
    limit: int = 100,
):

    verify_admin(admin)

    # --------------------------------------------------------
    # Protect limit
    # --------------------------------------------------------

    if limit < 1:
        limit = 1

    if limit > 500:
        limit = 500

    # --------------------------------------------------------
    # Fetch users
    # --------------------------------------------------------

    cursor = (
        users_collection
        .find({})
        .sort(
            [
                ("created_at", -1),
                ("_id", -1),
            ]
        )
        .limit(limit)
    )

    users = []

    async for user in cursor:

        user_id = user.pop("_id", None)

        if user_id is not None:

            user["id"] = str(user_id)

        # ----------------------------------------------------
        # Never send password information to frontend
        # ----------------------------------------------------

        user.pop("password", None)
        user.pop("password_hash", None)

        # ----------------------------------------------------
        # Convert ObjectId references safely
        # ----------------------------------------------------

        if user.get("user_id"):

            user["user_id"] = str(
                user["user_id"]
            )

        # ----------------------------------------------------
        # Convert datetime to JSON-safe ISO string
        # ----------------------------------------------------

        if user.get("created_at"):

            user["created_at"] = (
                user["created_at"].isoformat()
            )

        if user.get("updated_at"):

            user["updated_at"] = (
                user["updated_at"].isoformat()
            )

        users.append(user)

    return {
        "success": True,
        "users": users,
        "total": len(users),
    }


# ============================================================
# PREDICTION STATISTICS
# ============================================================

async def get_prediction_stats(
    admin: dict,
):

    verify_admin(admin)

    total = await predictions_collection.count_documents({})

    fake = await predictions_collection.count_documents({
        "label": "FAKE"
    })

    real = await predictions_collection.count_documents({
        "label": "REAL"
    })

    if total > 0:

        fake_percentage = (
            fake / total
        ) * 100

        real_percentage = (
            real / total
        ) * 100

    else:

        fake_percentage = 0
        real_percentage = 0

    return {
        "success": True,

        "predictions": {

            "total": total,

            "fake": fake,

            "real": real,

            "fake_percentage": round(
                fake_percentage,
                2,
            ),

            "real_percentage": round(
                real_percentage,
                2,
            ),
        },
    }


# ============================================================
# RECENT PREDICTIONS
# ============================================================

async def get_recent_predictions(
    admin: dict,
    limit: int = 10,
):

    verify_admin(admin)

    if limit < 1:
        limit = 1

    if limit > 50:
        limit = 50

    cursor = (
        predictions_collection
        .find({})
        .sort(
            [
                ("created_at", -1),
                ("_id", -1),
            ]
        )
        .limit(limit)
    )

    predictions = []

    async for prediction in cursor:

        prediction["id"] = str(
            prediction.pop("_id")
        )

        if prediction.get("user_id"):

            prediction["user_id"] = str(
                prediction["user_id"]
            )

        if prediction.get("created_at"):

            prediction["created_at"] = (
                prediction["created_at"].isoformat()
            )

        predictions.append(
            prediction
        )

    return {
        "success": True,
        "predictions": predictions,
    }
from pathlib import Path
from backend.routes.admin_routes import router as admin_router
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.database import (
    connect_to_database,
    close_database_connection
)

from backend.routes.prediction_routes import (
    router as prediction_router
)

from backend.routes.auth_routes import (
    router as auth_router
)


# ============================================================
# BASE DIRECTORY
# ============================================================

BASE_DIR = Path(
    __file__
).resolve().parent


# ============================================================
# DIRECTORIES
# ============================================================

UPLOAD_DIR = (
    BASE_DIR /
    "uploads"
)

GRADCAM_DIR = (
    BASE_DIR /
    "gradcam"
)

EXPLANATIONS_DIR = (
    BASE_DIR /
    "explanations"
)


# ============================================================
# CREATE DIRECTORIES
# ============================================================

UPLOAD_DIR.mkdir(
    parents=True,
    exist_ok=True
)

GRADCAM_DIR.mkdir(
    parents=True,
    exist_ok=True
)

EXPLANATIONS_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# FASTAPI
# ============================================================

app = FastAPI(

    title="TruthLens API",

    description=(
        "Multimodal Fake News Video Detection API "
        "using ResNet50, Whisper, BERT, XGBoost, "
        "SHAP and Grad-CAM."
    ),

    version="1.0.0"
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(

    CORSMiddleware,

    allow_origins=[

        "http://localhost:5173",

        "http://127.0.0.1:5173",

        "http://localhost:3000",

        "http://127.0.0.1:3000",

        "http://localhost:4173",

        "http://127.0.0.1:4173"

    ],

    allow_credentials=True,

    allow_methods=[
        "*"
    ],

    allow_headers=[
        "*"
    ]
)


# ============================================================
# STATIC FILES
# ============================================================

app.mount(

    "/uploads",

    StaticFiles(
        directory=str(
            UPLOAD_DIR
        )
    ),

    name="uploads"
)


# ============================================================
# GRAD-CAM
# ============================================================

app.mount(

    "/gradcam",

    StaticFiles(
        directory=str(
            GRADCAM_DIR
        )
    ),

    name="gradcam"
)


# ============================================================
# EXPLANATIONS
# ============================================================

app.mount(

    "/explanations",

    StaticFiles(
        directory=str(
            EXPLANATIONS_DIR
        )
    ),

    name="explanations"
)


# ============================================================
# API ROUTES
# ============================================================

app.include_router(
    auth_router
)
app.include_router(admin_router)

app.include_router(
    prediction_router
)


# ============================================================
# ROOT
# ============================================================

@app.get("/")
async def root():

    return {

        "success":
            True,

        "message":
            "TruthLens API is running.",

        "service":
            "Multimodal Fake News Video Detection",

        "version":
            "1.0.0"

    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
async def health():

    return {

        "success":
            True,

        "status":
            "healthy"

    }


# ============================================================
# API INFORMATION
# ============================================================

@app.get("/api")
async def api_info():

    return {

        "success":
            True,

        "message":
            "TruthLens API",

        "endpoints": {

            "register":
                "/api/auth/register",

            "login":
                "/api/auth/login",

            "current_user":
                "/api/auth/me",

            "prediction":
                "/api/predictions/predict",

            "health":
                "/health",

            "gradcam":
                "/gradcam/"

        }

    }


# ============================================================
# STARTUP
# ============================================================

@app.on_event(
    "startup"
)
async def startup_event():

    print()

    print(
        "=" * 70
    )

    print(
        "TRUTHLENS BACKEND"
    )

    print(
        "=" * 70
    )

    print(
        "Connecting to MongoDB..."
    )

    try:

        await connect_to_database()

    except Exception as error:

        print(
            "MongoDB connection failed:"
        )

        print(
            error
        )

    print()

    print(
        "API:",
        "http://127.0.0.1:8000"
    )

    print(
        "Authentication:",
        "http://127.0.0.1:8000/api/auth"
    )

    print(
        "Register:",
        "http://127.0.0.1:8000/api/auth/register"
    )

    print(
        "Login:",
        "http://127.0.0.1:8000/api/auth/login"
    )

    print(
        "Prediction:",
        "http://127.0.0.1:8000/api/predictions/predict"
    )

    print(
        "Grad-CAM:",
        "http://127.0.0.1:8000/gradcam/"
    )

    print(
        "Uploads:",
        "http://127.0.0.1:8000/uploads/"
    )

    print(
        "Health:",
        "http://127.0.0.1:8000/health"
    )

    print(
        "=" * 70
    )

    print()


# ============================================================
# SHUTDOWN
# ============================================================

@app.on_event(
    "shutdown"
)
async def shutdown_event():

    await close_database_connection()


# ============================================================
# LOCAL DEVELOPMENT
# ============================================================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(

        "backend.main:app",

        host="127.0.0.1",

        port=8000,

        reload=True

    )
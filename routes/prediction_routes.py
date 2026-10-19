
from fastapi import APIRouter, UploadFile, File
from pydantic import BaseModel

from backend.controllers.prediction_controller import (
    predict_uploaded_video,
    predict_direct_text,
)


router = APIRouter(
    prefix="/api/predictions",
    tags=["Predictions"]
)


# ============================================================
# TEXT REQUEST MODEL
# ============================================================

class TextPredictionRequest(BaseModel):
    text: str


# ============================================================
# EXISTING MULTIMODAL VIDEO PREDICTION
# ============================================================

@router.post("/predict")
async def predict_video(
    video: UploadFile = File(...)
):
    """
    Existing multimodal TruthLens detector.

    Video
      ↓
    ResNet50 + Whisper + BERT
      ↓
    2816 fused features
      ↓
    XGBoost
    """

    return await predict_uploaded_video(
        video
    )


# ============================================================
# NEW DIRECT TEXT-ONLY PREDICTION
# ============================================================

@router.post("/text-predict")
async def predict_text(
    request: TextPredictionRequest
):
    """
    Direct text-only TruthLens detector.

    Text
      ↓
    BERT
      ↓
    768 features
      ↓
    Text XGBoost
      ↓
    REAL / FAKE
    """

    return await predict_direct_text(
        request.text
    )



"""
============================================================
PREDICTION CONTROLLER
============================================================

Handles:

- Video upload
- Video validation
- Existing multimodal prediction
- Direct text-only prediction
- Prediction storage in MongoDB
- Temporary video cleanup
- Explanation response normalization

Endpoints using this controller:

1. POST /api/predictions/predict
   ResNet50 + Whisper + BERT + XGBoost

2. POST /api/predictions/text-predict
   Direct Text + BERT + Text XGBoost

IMPORTANT RESPONSE STRUCTURE:

Multimodal frontend expects:

prediction
├── label
├── fake_probability
├── real_probability
├── confidence
├── threshold
├── transcript
├── visual_feature_dimension
├── text_feature_dimension
├── fusion_feature_dimension
└── explanations
    ├── shap
    ├── gradcam
    ├── evidence_type
    ├── visual_contribution
    ├── text_contribution
    └── explanation_note

The prediction service generates Grad-CAM directly as:

result["gradcam"]

This controller converts it to:

result["explanations"]["gradcam"]

so that the existing frontend can consume it.
============================================================
"""

from datetime import datetime, timezone
from pathlib import Path
import uuid

from fastapi import (
    UploadFile,
    HTTPException,
)

from backend.services.prediction_service import (
    predict_video,
    predict_text,
)

from backend.database import (
    predictions_collection,
)


# ============================================================
# BASE DIRECTORY
# ============================================================

BASE_DIR = Path(
    __file__
).resolve().parents[2]


# ============================================================
# UPLOAD DIRECTORY
# ============================================================

UPLOAD_DIR = (
    BASE_DIR
    / "backend"
    / "uploads"
)

UPLOAD_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# ALLOWED VIDEO FORMATS
# ============================================================

ALLOWED_EXTENSIONS = {
    ".mp4",
    ".avi",
    ".mov",
    ".mkv",
    ".webm",
}


# ============================================================
# DEFAULT FEATURE DIMENSIONS
# ============================================================

DEFAULT_VISUAL_FEATURES = 2048
DEFAULT_TEXT_FEATURES = 768
DEFAULT_FUSION_FEATURES = 2816


# ============================================================
# DEFAULT THRESHOLDS
# ============================================================

MULTIMODAL_THRESHOLD = 0.30
TEXT_THRESHOLD = 0.39


# ============================================================
# HELPER FUNCTION
# ============================================================

async def _save_uploaded_video(
    video: UploadFile,
):
    """
    Validate and temporarily save an uploaded video.

    Returns:
        tuple:
            original filename
            generated filename
            saved video path
    """

    # ========================================================
    # VALIDATE FILENAME
    # ========================================================

    if not video.filename:

        raise HTTPException(
            status_code=400,
            detail="No video file provided.",
        )

    # ========================================================
    # VALIDATE EXTENSION
    # ========================================================

    extension = (
        Path(video.filename)
        .suffix
        .lower()
    )

    if extension not in ALLOWED_EXTENSIONS:

        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported video format. "
                "Use MP4, AVI, MOV, MKV or WEBM."
            ),
        )

    # ========================================================
    # CREATE TEMPORARY FILENAME
    # ========================================================

    filename = (
        f"{uuid.uuid4().hex}"
        f"{extension}"
    )

    video_path = (
        UPLOAD_DIR
        / filename
    )

    # ========================================================
    # READ UPLOADED VIDEO
    # ========================================================

    contents = await video.read()

    if not contents:

        raise HTTPException(
            status_code=400,
            detail="Uploaded video is empty.",
        )

    # ========================================================
    # SAVE VIDEO
    # ========================================================

    with open(
        video_path,
        "wb",
    ) as file:

        file.write(
            contents
        )

    return (
        video.filename,
        filename,
        video_path,
    )


# ============================================================
# EXPLANATION NORMALIZATION
# ============================================================

def _normalize_multimodal_result(
    result: dict,
):
    """
    Normalize the prediction_service response so that
    the existing frontend receives one consistent schema.

    prediction_service.py currently returns:

        result["shap_explanation"]
        result["gradcam"]
        result["feature_dimensions"]

    The frontend expects:

        result["explanations"]["shap"]
        result["explanations"]["gradcam"]

    and top-level feature dimensions.

    This function bridges that difference without changing
    prediction_service.py.
    """

    if not isinstance(
        result,
        dict,
    ):
        raise RuntimeError(
            "Prediction service returned an invalid result."
        )

    # ========================================================
    # EXISTING EXPLANATION OBJECT
    # ========================================================

    existing_explanations = result.get(
        "explanations",
        {},
    )

    if not isinstance(
        existing_explanations,
        dict,
    ):
        existing_explanations = {}

    # ========================================================
    # SHAP
    # ========================================================

    shap_explanation = result.get(
        "shap_explanation",
        existing_explanations.get(
            "shap",
            {
                "available": False,
            },
        ),
    )

    if not isinstance(
        shap_explanation,
        dict,
    ):
        shap_explanation = {
            "available": False,
            "reason": "Invalid SHAP explanation.",
        }

    # ========================================================
    # GRAD-CAM
    # ========================================================

    gradcam_result = result.get(
        "gradcam",
        existing_explanations.get(
            "gradcam",
            {
                "available": False,
                "frames_processed": 0,
                "requested_frames": 8,
                "frames": [],
            },
        ),
    )

    if not isinstance(
        gradcam_result,
        dict,
    ):
        gradcam_result = {
            "available": False,
            "frames_processed": 0,
            "requested_frames": 8,
            "frames": [],
            "error": "Invalid Grad-CAM response.",
        }

    # ========================================================
    # ENSURE GRAD-CAM DEFAULTS
    # ========================================================

    gradcam_result.setdefault(
        "available",
        False,
    )

    gradcam_result.setdefault(
        "frames_processed",
        0,
    )

    gradcam_result.setdefault(
        "requested_frames",
        8,
    )

    gradcam_result.setdefault(
        "frames",
        [],
    )

    # ========================================================
    # FEATURE DIMENSIONS
    # ========================================================

    feature_dimensions = result.get(
        "feature_dimensions",
        {},
    )

    if not isinstance(
        feature_dimensions,
        dict,
    ):
        feature_dimensions = {}

    visual_feature_dimension = int(
        result.get(
            "visual_feature_dimension",
            feature_dimensions.get(
                "resnet50",
                DEFAULT_VISUAL_FEATURES,
            ),
        )
    )

    text_feature_dimension = int(
        result.get(
            "text_feature_dimension",
            feature_dimensions.get(
                "bert",
                DEFAULT_TEXT_FEATURES,
            ),
        )
    )

    fusion_feature_dimension = int(
        result.get(
            "fusion_feature_dimension",
            feature_dimensions.get(
                "fused",
                DEFAULT_FUSION_FEATURES,
            ),
        )
    )

    # ========================================================
    # EVIDENCE INFORMATION
    # ========================================================

    evidence_type = existing_explanations.get(
        "evidence_type",
        "Multimodal",
    )

    visual_contribution = existing_explanations.get(
        "visual_contribution",
        shap_explanation.get(
            "visual_contribution_percent",
            0.0,
        ),
    )

    text_contribution = existing_explanations.get(
        "text_contribution",
        shap_explanation.get(
            "text_contribution_percent",
            0.0,
        ),
    )

    explanation_note = existing_explanations.get(
        "explanation_note",
        result.get(
            "human_readable_explanation",
            "",
        ),
    )

    # ========================================================
    # CREATE FRONTEND-COMPATIBLE EXPLANATIONS
    # ========================================================

    explanations = {

        "shap":
            shap_explanation,

        "gradcam":
            gradcam_result,

        "evidence_type":
            evidence_type,

        "visual_contribution":
            visual_contribution,

        "text_contribution":
            text_contribution,

        "explanation_note":
            explanation_note,
    }

    # ========================================================
    # ADD FRONTEND-COMPATIBLE TOP-LEVEL FIELDS
    # ========================================================

    result["visual_feature_dimension"] = (
        visual_feature_dimension
    )

    result["text_feature_dimension"] = (
        text_feature_dimension
    )

    result["fusion_feature_dimension"] = (
        fusion_feature_dimension
    )

    result["feature_dimensions"] = {

        "resnet50":
            visual_feature_dimension,

        "bert":
            text_feature_dimension,

        "fused":
            fusion_feature_dimension,
    }

    result["explanations"] = explanations

    # ========================================================
    # KEEP ORIGINAL SERVICE FIELDS TOO
    # ========================================================

    result["shap_explanation"] = (
        shap_explanation
    )

    result["gradcam"] = (
        gradcam_result
    )

    return result


# ============================================================
# EXISTING MULTIMODAL PREDICTION
# ============================================================

async def predict_uploaded_video(
    video: UploadFile,
):
    """
    Upload a video, run the existing TruthLens
    multimodal prediction pipeline, normalize the
    explanation structure, store the prediction in
    MongoDB, and return the result.

    Pipeline:

        Video
          ↓
        ResNet50
          ↓
       2048 visual features

        Video
          ↓
        Whisper
          ↓
       Transcript
          ↓
        BERT
          ↓
        768 text features

        2048 + 768
          ↓
        2816 fused features
          ↓
        XGBoost
          ↓
        REAL / FAKE

        ResNet50
          ↓
        Grad-CAM
          ↓
        8 explanation frames
    """

    video_path = None
    filename = None

    try:

        # ====================================================
        # SAVE UPLOADED VIDEO
        # ====================================================

        (
            original_filename,
            filename,
            video_path,
        ) = await _save_uploaded_video(
            video
        )

        print()
        print("=" * 70)
        print("MULTIMODAL VIDEO UPLOAD")
        print("=" * 70)

        print(
            "Original filename:",
            original_filename,
        )

        print(
            "Temporary file:",
            video_path,
        )

        # ====================================================
        # RUN EXISTING MULTIMODAL PREDICTION
        # ====================================================

        result = predict_video(
            str(video_path)
        )

        print(
            "Multimodal prediction completed."
        )

        # ====================================================
        # NORMALIZE RESULT
        # ====================================================

        result = _normalize_multimodal_result(
            result
        )

        # ====================================================
        # DEBUG GRAD-CAM
        # ====================================================

        gradcam = (
            result
            .get(
                "explanations",
                {},
            )
            .get(
                "gradcam",
                {},
            )
        )

        print()
        print(
            "Grad-CAM available:",
            gradcam.get(
                "available",
                False,
            ),
        )

        print(
            "Grad-CAM frames:",
            gradcam.get(
                "frames_processed",
                0,
            ),
        )

        print(
            "Grad-CAM frame list:",
            len(
                gradcam.get(
                    "frames",
                    [],
                )
            ),
        )

        # ====================================================
        # EXTRACT LABEL
        # ====================================================

        label = str(
            result.get(
                "label",
                "",
            )
        ).strip().upper()

        if label not in {
            "FAKE",
            "REAL",
        }:

            raise RuntimeError(
                "Prediction returned an invalid label."
            )

        # ====================================================
        # CREATE MONGODB DOCUMENT
        # ====================================================

        prediction_document = {

            "detector":
                "MULTIMODAL",

            "model":
                "ResNet50 + Whisper + BERT + XGBoost",

            "filename":
                original_filename,

            "stored_filename":
                filename,

            "label":
                label,

            "fake_probability":
                float(
                    result.get(
                        "fake_probability",
                        0.0,
                    )
                ),

            "real_probability":
                float(
                    result.get(
                        "real_probability",
                        0.0,
                    )
                ),

            "confidence":
                float(
                    result.get(
                        "confidence",
                        0.0,
                    )
                ),

            "threshold":
                float(
                    result.get(
                        "threshold",
                        MULTIMODAL_THRESHOLD,
                    )
                ),

            "reason":
                result.get(
                    "reason",
                    "",
                ),

            "human_readable_explanation":
                result.get(
                    "human_readable_explanation",
                    "",
                ),

            "transcript":
                result.get(
                    "transcript",
                    "",
                ),

            # ------------------------------------------------
            # FEATURE DIMENSIONS
            # ------------------------------------------------

            "visual_feature_dimension":
                int(
                    result.get(
                        "visual_feature_dimension",
                        DEFAULT_VISUAL_FEATURES,
                    )
                ),

            "text_feature_dimension":
                int(
                    result.get(
                        "text_feature_dimension",
                        DEFAULT_TEXT_FEATURES,
                    )
                ),

            "fusion_feature_dimension":
                int(
                    result.get(
                        "fusion_feature_dimension",
                        DEFAULT_FUSION_FEATURES,
                    )
                ),

            "feature_dimensions":
                result.get(
                    "feature_dimensions",
                    {
                        "resnet50":
                            DEFAULT_VISUAL_FEATURES,

                        "bert":
                            DEFAULT_TEXT_FEATURES,

                        "fused":
                            DEFAULT_FUSION_FEATURES,
                    },
                ),

            # ------------------------------------------------
            # NORMALIZED EXPLANATIONS
            # ------------------------------------------------

            "explanations":
                result.get(
                    "explanations",
                    {},
                ),

            # ------------------------------------------------
            # KEEP ORIGINAL EXPLANATION FIELDS
            # ------------------------------------------------

            "shap_explanation":
                result.get(
                    "shap_explanation",
                    {},
                ),

            "gradcam":
                result.get(
                    "gradcam",
                    {},
                ),

            # ------------------------------------------------
            # TIMESTAMP
            # ------------------------------------------------

            "created_at":
                datetime.now(
                    timezone.utc
                ),
        }

        # ====================================================
        # SAVE TO MONGODB
        # ====================================================

        insert_result = (
            await predictions_collection.insert_one(
                prediction_document
            )
        )

        prediction_id = str(
            insert_result.inserted_id
        )

        print(
            "Multimodal prediction saved to MongoDB."
        )

        print(
            "Prediction ID:",
            prediction_id,
        )

        # ====================================================
        # RESPONSE
        # ====================================================

        return {

            "success":
                True,

            "filename":
                original_filename,

            "prediction_id":
                prediction_id,

            "detector":
                "MULTIMODAL",

            "prediction":
                result,
        }

    except HTTPException:

        raise

    except Exception as e:

        print()
        print(
            "Multimodal prediction error:",
            repr(e),
        )

        raise HTTPException(
            status_code=500,
            detail=str(e),
        )

    finally:

        # ====================================================
        # DELETE TEMPORARY VIDEO
        # ====================================================

        if (
            video_path is not None
            and video_path.exists()
        ):

            try:

                video_path.unlink()

                print(
                    "Temporary multimodal upload deleted."
                )

            except Exception as e:

                print(
                    "Could not delete temporary "
                    f"video: {e}"
                )


# ============================================================
# DIRECT TEXT-ONLY PREDICTION
# ============================================================

async def predict_direct_text(
    text: str,
):
    """
    Run the independent text-only TruthLens detector.

    IMPORTANT:
        This endpoint accepts DIRECT TEXT ONLY.

    It does NOT:
        - upload a video
        - use Whisper
        - use ResNet50
        - use the multimodal XGBoost model
        - generate Grad-CAM
        - generate video-based SHAP explanations

    Pipeline:

        Direct Text
             ↓
           BERT
             ↓
        768 features
             ↓
       Text XGBoost
             ↓
        REAL / FAKE

    Text classification threshold:
        0.39
    """

    try:

        # ====================================================
        # VALIDATE TEXT
        # ====================================================

        if not isinstance(
            text,
            str,
        ):

            raise HTTPException(
                status_code=400,
                detail="Text must be a string.",
            )

        text = text.strip()

        if not text:

            raise HTTPException(
                status_code=400,
                detail="Text input cannot be empty.",
            )

        # ====================================================
        # DEBUG INFORMATION
        # ====================================================

        print()
        print("=" * 70)
        print("DIRECT TEXT-ONLY PREDICTION")
        print("=" * 70)

        print(
            "Input text length:",
            len(text),
        )

        # ====================================================
        # RUN TEXT-ONLY MODEL
        # ====================================================

        result = predict_text(
            text
        )

        print(
            "Text-only prediction completed."
        )

        # ====================================================
        # EXTRACT LABEL
        # ====================================================

        label = str(
            result.get(
                "label",
                "",
            )
        ).strip().upper()

        if label not in {
            "FAKE",
            "REAL",
        }:

            raise RuntimeError(
                "Text-only prediction returned "
                "an invalid label."
            )

        # ====================================================
        # NORMALIZE TEXT FEATURE DIMENSION
        # ====================================================

        text_feature_dimension = int(
            result.get(
                "text_feature_dimension",
                result.get(
                    "feature_dimensions",
                    {}
                ).get(
                    "bert",
                    DEFAULT_TEXT_FEATURES,
                )
                if isinstance(
                    result.get(
                        "feature_dimensions",
                        {},
                    ),
                    dict,
                )
                else DEFAULT_TEXT_FEATURES,
            )
        )

        result["text_feature_dimension"] = (
            text_feature_dimension
        )

        result["feature_dimensions"] = {
            "bert":
                text_feature_dimension,
        }

        # ====================================================
        # CREATE TEXT EXPLANATIONS
        # ====================================================

        existing_explanations = result.get(
            "explanations",
            {},
        )

        if not isinstance(
            existing_explanations,
            dict,
        ):
            existing_explanations = {}

        result["explanations"] = (
            existing_explanations
        )

        # ====================================================
        # CREATE MONGODB DOCUMENT
        # ====================================================

        prediction_document = {

            # ------------------------------------------------
            # DETECTOR
            # ------------------------------------------------

            "detector":
                "TEXT_ONLY",

            "model":
                "BERT + Text XGBoost",

            # ------------------------------------------------
            # INPUT
            # ------------------------------------------------

            "input_type":
                "DIRECT_TEXT",

            "input_text":
                text,

            # ------------------------------------------------
            # RESULT
            # ------------------------------------------------

            "label":
                label,

            "fake_probability":
                float(
                    result.get(
                        "fake_probability",
                        0.0,
                    )
                ),

            "real_probability":
                float(
                    result.get(
                        "real_probability",
                        0.0,
                    )
                ),

            "confidence":
                float(
                    result.get(
                        "confidence",
                        0.0,
                    )
                ),

            "threshold":
                float(
                    result.get(
                        "threshold",
                        TEXT_THRESHOLD,
                    )
                ),

            # ------------------------------------------------
            # FEATURE INFORMATION
            # ------------------------------------------------

            "feature_type":
                "TEXT",

            "text_feature_dimension":
                text_feature_dimension,

            "feature_dimensions":
                result.get(
                    "feature_dimensions",
                    {
                        "bert":
                            text_feature_dimension,
                    },
                ),

            # ------------------------------------------------
            # EXPLANATION
            # ------------------------------------------------

            "reason":
                result.get(
                    "reason",
                    "",
                ),

            "human_readable_explanation":
                result.get(
                    "human_readable_explanation",
                    "",
                ),

            "explanations":
                result.get(
                    "explanations",
                    {},
                ),

            # ------------------------------------------------
            # TIMESTAMP
            # ------------------------------------------------

            "created_at":
                datetime.now(
                    timezone.utc
                ),
        }

        # ====================================================
        # SAVE TO MONGODB
        # ====================================================

        insert_result = (
            await predictions_collection.insert_one(
                prediction_document
            )
        )

        prediction_id = str(
            insert_result.inserted_id
        )

        print(
            "Text-only prediction saved to MongoDB."
        )

        print(
            "Prediction ID:",
            prediction_id,
        )

        # ====================================================
        # RESPONSE
        # ====================================================

        return {

            "success":
                True,

            "prediction_id":
                prediction_id,

            "detector":
                "TEXT_ONLY",

            "prediction":
                result,
        }

    except HTTPException:

        raise

    except Exception as e:

        print()
        print(
            "Text-only prediction error:",
            repr(e),
        )

        raise HTTPException(
            status_code=500,
            detail=str(e),
        )



import os
import traceback

import numpy as np
import xgboost as xgb
import shap

from backend.models.bert_model import extract_text_features
from models.visual_model import extract_visual_features
from models.gradcam import generate_gradcam
from backend.services.evidence_analyzer import (
    generate_human_explanation
)


# ============================================================
# BASE DIRECTORY
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)


# ============================================================
# MODEL PATHS
# ============================================================

MULTIMODAL_MODEL_PATH = os.path.join(
    BASE_DIR,
    "models",
    "xgboost_fusion_model.json"
)

TEXT_MODEL_PATH = os.path.join(
    BASE_DIR,
    "models",
    "text_xgboost_model.json"
)


# ============================================================
# FEATURE DIMENSIONS
# ============================================================

RESNET_FEATURES = 2048

BERT_FEATURES = 768

EXPECTED_FEATURES = 2816

TOP_SHAP_FEATURES = 10


# ============================================================
# THRESHOLDS
# ============================================================

# Current multimodal production/reporting threshold
FAKE_THRESHOLD = 0.30

# Current text-only threshold
TEXT_FAKE_THRESHOLD = 0.39


# ============================================================
# LOAD MULTIMODAL XGBOOST MODEL
# ============================================================

print()
print("=" * 70)
print("LOADING MULTIMODAL XGBOOST MODEL")
print("=" * 70)

print(
    "Model path:",
    MULTIMODAL_MODEL_PATH
)

xgb_model = xgb.XGBClassifier()

xgb_model.load_model(
    MULTIMODAL_MODEL_PATH
)

print(
    "XGBoost model loaded successfully."
)

print(
    "XGBoost classes:",
    xgb_model.classes_
)

try:

    model_feature_count = (
        xgb_model.get_booster()
        .num_features()
    )

    print(
        "XGBoost feature count:",
        model_feature_count
    )

    if model_feature_count != EXPECTED_FEATURES:

        print(
            "WARNING: XGBoost model feature "
            f"count is {model_feature_count}, "
            f"expected {EXPECTED_FEATURES}."
        )

except Exception as error:

    print(
        "WARNING: Could not determine "
        "XGBoost feature count:",
        error
    )


# ============================================================
# LOAD TEXT-ONLY XGBOOST MODEL
# ============================================================

print()
print("=" * 70)
print("LOADING TEXT-ONLY XGBOOST MODEL")
print("=" * 70)

print(
    "Text model path:",
    TEXT_MODEL_PATH
)

text_xgb_model = xgb.XGBClassifier()

text_xgb_model.load_model(
    TEXT_MODEL_PATH
)

print(
    "Text-only XGBoost model "
    "loaded successfully."
)

print(
    "Text XGBoost classes:",
    text_xgb_model.classes_
)


# ============================================================
# SHAP TREE EXPLAINER
# ============================================================

print()
print("=" * 70)
print("INITIALIZING SHAP TREEEXPLAINER")
print("=" * 70)

try:

    shap_explainer = shap.TreeExplainer(
        xgb_model
    )

    print(
        "SHAP TreeExplainer "
        "created successfully."
    )

except Exception as error:

    shap_explainer = None

    print(
        "WARNING: SHAP TreeExplainer "
        "initialization failed."
    )

    print(
        "Error:",
        repr(error)
    )


# ============================================================
# FEATURE NAMES
# ============================================================

def _get_shap_feature_names():

    feature_names = []

    # --------------------------------------------------------
    # ResNet50: 2048 features
    # --------------------------------------------------------

    for i in range(
        RESNET_FEATURES
    ):

        feature_names.append(
            f"ResNet50_Feature_{i + 1}"
        )

    # --------------------------------------------------------
    # BERT: 768 features
    # --------------------------------------------------------

    for i in range(
        BERT_FEATURES
    ):

        feature_names.append(
            f"BERT_Feature_{i + 1}"
        )

    return feature_names


# ============================================================
# NORMALIZE SHAP OUTPUT
# ============================================================

def _normalize_shap_values(
    raw_shap_values
):

    """
    Normalize SHAP output from different
    SHAP library versions.

    Supported forms:

        list[class_0, class_1]

        Explanation object

        (samples, features)

        (samples, features, classes)

        (samples, classes, features)
    """

    print(
        "[SHAP] Raw output type:",
        type(raw_shap_values).__name__
    )

    # --------------------------------------------------------
    # Older SHAP versions may return a list
    # --------------------------------------------------------

    if isinstance(
        raw_shap_values,
        list
    ):

        print(
            "[SHAP] Output is a list."
        )

        print(
            "[SHAP] Number of class outputs:",
            len(raw_shap_values)
        )

        if len(raw_shap_values) == 0:

            raise RuntimeError(
                "SHAP returned an empty list."
            )

        if len(raw_shap_values) > 1:

            raw_shap_values = (
                raw_shap_values[1]
            )

            print(
                "[SHAP] Using class-1 "
                "(FAKE) SHAP values."
            )

        else:

            raw_shap_values = (
                raw_shap_values[0]
            )

    # --------------------------------------------------------
    # Newer SHAP versions return Explanation
    # --------------------------------------------------------

    if hasattr(
        raw_shap_values,
        "values"
    ):

        print(
            "[SHAP] Explanation object detected."
        )

        raw_shap_values = (
            raw_shap_values.values
        )

    # --------------------------------------------------------
    # Convert to NumPy
    # --------------------------------------------------------

    shap_values = np.asarray(
        raw_shap_values
    )

    print(
        "[SHAP] Converted shape:",
        shap_values.shape
    )

    # --------------------------------------------------------
    # Three-dimensional output
    # --------------------------------------------------------

    if shap_values.ndim == 3:

        print(
            "[SHAP] 3D SHAP output detected."
        )

        # ----------------------------------------------------
        # Shape:
        # (samples, features, classes)
        # ----------------------------------------------------

        if (
            shap_values.shape[-1] == 2
        ):

            print(
                "[SHAP] Selecting class 1 "
                "from final dimension."
            )

            shap_values = (
                shap_values[:, :, 1]
            )

        # ----------------------------------------------------
        # Shape:
        # (samples, classes, features)
        # ----------------------------------------------------

        elif (
            shap_values.shape[1] == 2
        ):

            print(
                "[SHAP] Selecting class 1 "
                "from middle dimension."
            )

            shap_values = (
                shap_values[:, 1, :]
            )

        else:

            raise RuntimeError(
                "Unexpected 3D SHAP shape: "
                f"{shap_values.shape}"
            )

    # --------------------------------------------------------
    # Validate final dimensions
    # --------------------------------------------------------

    if shap_values.ndim != 2:

        raise RuntimeError(
            "Unexpected SHAP dimensions: "
            f"{shap_values.shape}"
        )

    if (
        shap_values.shape[1]
        != EXPECTED_FEATURES
    ):

        raise RuntimeError(
            "Unexpected SHAP feature "
            f"dimension: {shap_values.shape[1]}. "
            f"Expected {EXPECTED_FEATURES}."
        )

    return shap_values


# ============================================================
# SHAP EXPLANATION
# ============================================================

def calculate_shap_explanation(
    model_input
):

    print()
    print("-" * 70)
    print("SHAP EXPLANATION")
    print("-" * 70)

    # --------------------------------------------------------
    # Validate explainer
    # --------------------------------------------------------

    if shap_explainer is None:

        print(
            "[SHAP] Explainer unavailable."
        )

        return {

            "available":
                False,

            "feature_dimension":
                EXPECTED_FEATURES,

            "visual_features":
                RESNET_FEATURES,

            "text_features":
                BERT_FEATURES,

            "visual_percentage":
                0.0,

            "text_percentage":
                0.0,

            "dominant_modality":
                "Unavailable",

            "top_features":
                [],

            "reason":
                "SHAP TreeExplainer "
                "is not available."

        }

    try:

        # ----------------------------------------------------
        # Convert input
        # ----------------------------------------------------

        model_input = np.asarray(
            model_input,
            dtype=np.float32
        )

        if model_input.ndim == 1:

            model_input = (
                model_input.reshape(
                    1,
                    -1
                )
            )

        print(
            "[SHAP] Input shape:",
            model_input.shape
        )

        # ----------------------------------------------------
        # Validate dimensions
        # ----------------------------------------------------

        if model_input.ndim != 2:

            raise ValueError(
                "SHAP input must be "
                "2-dimensional."
            )

        if (
            model_input.shape[1]
            != EXPECTED_FEATURES
        ):

            raise ValueError(
                "SHAP received invalid "
                f"feature dimension: "
                f"{model_input.shape[1]}. "
                f"Expected "
                f"{EXPECTED_FEATURES}."
            )

        # ----------------------------------------------------
        # Calculate SHAP
        # ----------------------------------------------------

        print(
            "[SHAP] Calculating values..."
        )

        raw_shap_values = (
            shap_explainer.shap_values(
                model_input
            )
        )

        print(
            "[SHAP] Values calculated."
        )

        # ----------------------------------------------------
        # Normalize SHAP output
        # ----------------------------------------------------

        shap_values = (
            _normalize_shap_values(
                raw_shap_values
            )
        )

        print(
            "[SHAP] Final SHAP shape:",
            shap_values.shape
        )

        # ----------------------------------------------------
        # One uploaded video
        # ----------------------------------------------------

        values = shap_values[0]

        # ----------------------------------------------------
        # Feature names
        # ----------------------------------------------------

        feature_names = (
            _get_shap_feature_names()
        )

        # ----------------------------------------------------
        # Absolute SHAP values
        # ----------------------------------------------------

        absolute_values = np.abs(
            values
        )

        # ====================================================
        # VISUAL MODALITY
        # ====================================================

        visual_values = values[
            :RESNET_FEATURES
        ]

        # ====================================================
        # TEXT MODALITY
        # ====================================================

        text_values = values[
            RESNET_FEATURES:
        ]

        # ----------------------------------------------------
        # Absolute modality importance
        # ----------------------------------------------------

        visual_importance = float(
            np.sum(
                np.abs(
                    visual_values
                )
            )
        )

        text_importance = float(
            np.sum(
                np.abs(
                    text_values
                )
            )
        )

        total_importance = (
            visual_importance
            +
            text_importance
        )

        # ----------------------------------------------------
        # Modality percentages
        # ----------------------------------------------------

        if total_importance > 0:

            visual_percentage = float(
                (
                    visual_importance
                    /
                    total_importance
                )
                * 100
            )

            text_percentage = float(
                (
                    text_importance
                    /
                    total_importance
                )
                * 100
            )

        else:

            visual_percentage = 0.0

            text_percentage = 0.0

        # ----------------------------------------------------
        # Dominant modality
        # ----------------------------------------------------

        if (
            visual_importance
            >
            text_importance
        ):

            dominant_modality = (
                "ResNet50"
            )

        elif (
            text_importance
            >
            visual_importance
        ):

            dominant_modality = (
                "BERT"
            )

        else:

            dominant_modality = (
                "Balanced"
            )

        # ====================================================
        # TOP SHAP FEATURES
        # ====================================================

        top_indices = np.argsort(
            absolute_values
        )[::-1][
            :TOP_SHAP_FEATURES
        ]

        top_features = []

        for rank, index in enumerate(
            top_indices,
            start=1
        ):

            index = int(
                index
            )

            shap_value = float(
                values[index]
            )

            absolute_shap = float(
                absolute_values[index]
            )

            # ------------------------------------------------
            # Direction
            # ------------------------------------------------

            if shap_value > 0:

                direction = "FAKE"

            elif shap_value < 0:

                direction = "REAL"

            else:

                direction = "NEUTRAL"

            # ------------------------------------------------
            # Modality
            # ------------------------------------------------

            if index < RESNET_FEATURES:

                modality = "ResNet50"

            else:

                modality = "BERT"

            feature_name = (
                feature_names[index]
            )

            top_features.append({

                "rank":
                    int(rank),

                "feature":
                    feature_name,

                "feature_name":
                    feature_name,

                "feature_index":
                    index,

                "modality":
                    modality,

                "shap_value":
                    shap_value,

                "absolute_shap":
                    absolute_shap,

                "absolute_shap_value":
                    absolute_shap,

                "direction":
                    direction

            })

        # ====================================================
        # RESULT
        # ====================================================

        result = {

            "available":
                True,

            "method":
                "SHAP TreeExplainer",

            "feature_dimension":
                EXPECTED_FEATURES,

            "visual_features":
                RESNET_FEATURES,

            "text_features":
                BERT_FEATURES,

            "visual_mean_absolute_shap":
                float(
                    np.mean(
                        np.abs(
                            visual_values
                        )
                    )
                ),

            "text_mean_absolute_shap":
                float(
                    np.mean(
                        np.abs(
                            text_values
                        )
                    )
                ),

            "visual_absolute_importance":
                visual_importance,

            "text_absolute_importance":
                text_importance,

            "visual_percentage":
                round(
                    visual_percentage,
                    2
                ),

            "text_percentage":
                round(
                    text_percentage,
                    2
                ),

            # Backward compatibility
            "visual_contribution_percent":
                round(
                    visual_percentage,
                    2
                ),

            "text_contribution_percent":
                round(
                    text_percentage,
                    2
                ),

            "dominant_modality":
                dominant_modality,

            "top_features":
                top_features

        }

        # ----------------------------------------------------
        # Console output
        # ----------------------------------------------------

        print(
            "[SHAP] Visual contribution:",
            f"{visual_percentage:.2f}%"
        )

        print(
            "[SHAP] Text contribution:",
            f"{text_percentage:.2f}%"
        )

        print(
            "[SHAP] Dominant modality:",
            dominant_modality
        )

        print(
            "[SHAP] Top features:",
            len(top_features)
        )

        for item in top_features[:3]:

            print(
                "[SHAP] Top:",
                item["feature"],
                "|",
                item["modality"],
                "|",
                item["direction"],
                "|",
                round(
                    item["shap_value"],
                    6
                )
            )

        print(
            "[SHAP] Explanation successful."
        )

        return result

    except Exception as error:

        print(
            "[SHAP ERROR]",
            repr(error)
        )

        traceback.print_exc()

        return {

            "available":
                False,

            "method":
                "SHAP TreeExplainer",

            "feature_dimension":
                EXPECTED_FEATURES,

            "visual_features":
                RESNET_FEATURES,

            "text_features":
                BERT_FEATURES,

            "visual_percentage":
                0.0,

            "text_percentage":
                0.0,

            "dominant_modality":
                "Unavailable",

            "top_features":
                [],

            "error":
                str(error),

            "error_type":
                type(error).__name__

        }


# ============================================================
# HUMAN-READABLE REASON
# ============================================================

def create_user_reason(
    label,
    evidence_result
):

    label = str(
        label
    ).upper()

    if not isinstance(
        evidence_result,
        dict
    ):

        evidence_result = {}

    evidence_type = (
        evidence_result.get(
            "dominant_modality",
            "Balanced"
        )
    )

    # Support both old and new modality names
    if evidence_type == "ResNet50":

        evidence_type = "Visual"

    elif evidence_type == "BERT":

        evidence_type = "Text"

    if label == "FAKE":

        if evidence_type == "Visual":

            return (
                "The video was classified "
                "as FAKE. Visual features "
                "contributed more strongly "
                "to the model's decision."
            )

        if evidence_type == "Text":

            return (
                "The video was classified "
                "as FAKE. Textual features "
                "contributed more strongly "
                "to the model's decision."
            )

        return (
            "The video was classified as "
            "FAKE based on combined "
            "visual and textual features."
        )

    if evidence_type == "Visual":

        return (
            "The video was classified "
            "as REAL. Visual features "
            "contributed more strongly "
            "to the model's decision."
        )

    if evidence_type == "Text":

        return (
            "The video was classified "
            "as REAL. Textual features "
            "contributed more strongly "
            "to the model's decision."
        )

    return (
        "The video was classified as "
        "REAL based on combined "
        "visual and textual features."
    )


# ============================================================
# MULTIMODAL VIDEO PREDICTION
# ============================================================

def predict_video(
    video_path
):

    """
    Multimodal TruthLens detector.

    Video
      ↓
    Whisper
      ↓
    Transcript
      ↓
    BERT → 768
      +
    ResNet50 → 2048
      ↓
    2816 fused features
      ↓
    XGBoost
      ↓
    REAL / FAKE

    Explainability:

    2816 fused features
      ↓
    SHAP TreeExplainer

    Video frames
      ↓
    ResNet50 Grad-CAM
    """

    from backend.models.whisper_model import (
        transcribe_audio
    )

    print()
    print("=" * 70)
    print("MULTIMODAL VIDEO PREDICTION")
    print("=" * 70)

    # ========================================================
    # WHISPER
    # ========================================================

    transcript = transcribe_audio(
        video_path
    )

    if transcript is None:

        transcript = ""

    transcript = str(
        transcript
    ).strip()

    # ========================================================
    # BERT
    # ========================================================

    bert_features = extract_text_features(
        transcript
    )

    bert_features = np.asarray(
        bert_features,
        dtype=np.float32
    )

    if bert_features.ndim > 1:

        bert_features = (
            bert_features.reshape(-1)
        )

    print(
        "BERT feature dimension:",
        len(bert_features)
    )

    if (
        len(bert_features)
        != BERT_FEATURES
    ):

        raise ValueError(
            "BERT feature dimension "
            f"mismatch. Expected "
            f"{BERT_FEATURES}, received "
            f"{len(bert_features)}."
        )

    # ========================================================
    # RESNET50
    # ========================================================

    print(
        "Extracting visual features from:",
        video_path
    )

    resnet_features = (
        extract_visual_features(
            video_path
        )
    )

    resnet_features = np.asarray(
        resnet_features,
        dtype=np.float32
    )

    if resnet_features.ndim > 1:

        resnet_features = (
            resnet_features.reshape(-1)
        )

    print(
        "ResNet50 feature dimension:",
        len(resnet_features)
    )

    if (
        len(resnet_features)
        != RESNET_FEATURES
    ):

        raise ValueError(
            "ResNet50 feature "
            f"dimension mismatch. "
            f"Expected "
            f"{RESNET_FEATURES}, "
            f"received "
            f"{len(resnet_features)}."
        )

    # ========================================================
    # FEATURE FUSION
    # ========================================================

    fused_features = np.concatenate(
        [
            resnet_features,
            bert_features
        ]
    ).astype(
        np.float32
    )

    print(
        "Fused feature dimension:",
        len(fused_features)
    )

    if (
        len(fused_features)
        != EXPECTED_FEATURES
    ):

        raise ValueError(
            "Fused feature dimension "
            f"mismatch. Expected "
            f"{EXPECTED_FEATURES}, "
            f"received "
            f"{len(fused_features)}."
        )

    model_input = (
        fused_features.reshape(
            1,
            -1
        )
    )

    # ========================================================
    # XGBOOST PREDICTION
    # ========================================================

    probabilities = (
        xgb_model.predict_proba(
            model_input
        )[0]
    )

    classes = list(
        xgb_model.classes_
    )

    real_index = classes.index(
        0
    )

    fake_index = classes.index(
        1
    )

    real_probability = float(
        probabilities[
            real_index
        ]
    )

    fake_probability = float(
        probabilities[
            fake_index
        ]
    )

    # ========================================================
    # THRESHOLD
    # ========================================================

    if (
        fake_probability
        >= FAKE_THRESHOLD
    ):

        label = "FAKE"

    else:

        label = "REAL"

    confidence = (
        fake_probability
        if label == "FAKE"
        else real_probability
    )

    print(
        "Fake probability:",
        round(
            fake_probability,
            4
        )
    )

    print(
        "Real probability:",
        round(
            real_probability,
            4
        )
    )

    print(
        "Threshold:",
        FAKE_THRESHOLD
    )

    print(
        "Prediction:",
        label
    )

    # ========================================================
    # SHAP
    # ========================================================

    shap_explanation = (
        calculate_shap_explanation(
            model_input
        )
    )

    # ========================================================
    # GRAD-CAM
    # ========================================================

    # IMPORTANT:
    # Keep using the existing working Grad-CAM module.
    # Do not change its /gradcam/ output route.

    gradcam_output_dir = os.path.join(
        BASE_DIR,
        "backend",
        "gradcam"
    )

    try:

        os.makedirs(
            gradcam_output_dir,
            exist_ok=True
        )

        print()
        print(
            "[Grad-CAM] Starting generation..."
        )

        print(
            "[Grad-CAM] Video:",
            video_path
        )

        print(
            "[Grad-CAM] Output directory:",
            gradcam_output_dir
        )

        gradcam_result = generate_gradcam(
            video_path=video_path,
            output_dir=gradcam_output_dir,
            max_frames=8
        )

        if not isinstance(
            gradcam_result,
            dict
        ):

            raise TypeError(
                "generate_gradcam() must "
                "return a dictionary; "
                f"received "
                f"{type(gradcam_result).__name__}."
            )

        gradcam_result.setdefault(
            "available",
            False
        )

        gradcam_result.setdefault(
            "frames_processed",
            0
        )

        gradcam_result.setdefault(
            "requested_frames",
            8
        )

        gradcam_result.setdefault(
            "frames",
            []
        )

        print(
            "[Grad-CAM] Finished. "
            f"Available: "
            f"{gradcam_result.get('available')}; "
            f"Frames processed: "
            f"{gradcam_result.get('frames_processed')}"
        )

    except Exception as error:

        print(
            "[Grad-CAM ERROR]",
            repr(error)
        )

        traceback.print_exc()

        gradcam_result = {

            "available":
                False,

            "frames_processed":
                0,

            "requested_frames":
                8,

            "frames":
                [],

            "error":
                str(error),

            "error_type":
                type(error).__name__

        }

    # ========================================================
    # HUMAN EXPLANATION
    # ========================================================

    try:

        human_explanation = (
            generate_human_explanation(
                label=label,
                transcript=transcript,
                fake_probability=fake_probability,
                real_probability=real_probability
            )
        )

    except Exception as error:

        print(
            "[Human Explanation ERROR]",
            repr(error)
        )

        human_explanation = (
            create_user_reason(
                label,
                shap_explanation
            )
        )

    # ========================================================
    # EXPLANATIONS OBJECT
    # ========================================================

    explanations = {

        "shap":
            shap_explanation,

        "gradcam":
            gradcam_result

    }

    # ========================================================
    # RESULT
    # ========================================================

    result = {

        "detector":
            "MULTIMODAL",

        "model":
            "ResNet50 + Whisper + BERT + XGBoost",

        "label":
            label,

        "fake_probability":
            round(
                fake_probability,
                4
            ),

        "real_probability":
            round(
                real_probability,
                4
            ),

        "confidence":
            round(
                confidence,
                4
            ),

        "threshold":
            FAKE_THRESHOLD,

        "transcript":
            transcript,

        # ----------------------------------------------------
        # Feature dimensions
        # ----------------------------------------------------

        "feature_dimensions": {

            "resnet50":
                RESNET_FEATURES,

            "bert":
                BERT_FEATURES,

            "fused":
                EXPECTED_FEATURES

        },

        # ----------------------------------------------------
        # Top-level aliases retained for compatibility
        # ----------------------------------------------------

        "visual_feature_dimension":
            RESNET_FEATURES,

        "text_feature_dimension":
            BERT_FEATURES,

        "fusion_feature_dimension":
            EXPECTED_FEATURES,

        # ----------------------------------------------------
        # New unified explanation structure
        # ----------------------------------------------------

        "explanations":
            explanations,

        # ----------------------------------------------------
        # Existing fields retained
        # ----------------------------------------------------

        "shap_explanation":
            shap_explanation,

        "gradcam":
            gradcam_result,

        "human_readable_explanation":
            human_explanation,

        "reason":
            create_user_reason(
                label,
                shap_explanation
            )

    }

    # ========================================================
    # FINAL DEBUG
    # ========================================================

    print()
    print("=" * 70)
    print("MULTIMODAL PREDICTION COMPLETED")
    print("=" * 70)

    print(
        "SHAP available:",
        result[
            "explanations"
        ][
            "shap"
        ].get(
            "available",
            False
        )
    )

    print(
        "SHAP top features:",
        len(
            result[
                "explanations"
            ][
                "shap"
            ].get(
                "top_features",
                []
            )
        )
    )

    print(
        "Grad-CAM available:",
        result[
            "explanations"
        ][
            "gradcam"
        ].get(
            "available",
            False
        )
    )

    print(
        "Grad-CAM frames:",
        result[
            "explanations"
        ][
            "gradcam"
        ].get(
            "frames_processed",
            0
        )
    )

    return result


# ============================================================
# TEXT-ONLY DETECTION
# ============================================================

def predict_text(
    text: str
):

    """
    Direct text-only fake-news detection.

    Text
      ↓
    BERT → 768 features
      ↓
    Text XGBoost
      ↓
    REAL / FAKE
    """

    # ========================================================
    # VALIDATE INPUT
    # ========================================================

    if text is None:

        raise ValueError(
            "Text input is required."
        )

    text = str(
        text
    ).strip()

    if not text:

        raise ValueError(
            "Text input cannot be empty."
        )

    # ========================================================
    # BERT
    # ========================================================

    bert_features = extract_text_features(
        text
    )

    bert_features = np.asarray(
        bert_features,
        dtype=np.float32
    )

    if bert_features.ndim > 1:

        bert_features = (
            bert_features.reshape(-1)
        )

    if (
        len(bert_features)
        != BERT_FEATURES
    ):

        raise ValueError(
            "BERT feature dimension "
            f"mismatch. Expected "
            f"{BERT_FEATURES}, received "
            f"{len(bert_features)}."
        )

    model_input = (
        bert_features.reshape(
            1,
            -1
        )
    )

    # ========================================================
    # TEXT XGBOOST
    # ========================================================

    probabilities = (
        text_xgb_model.predict_proba(
            model_input
        )[0]
    )

    classes = list(
        text_xgb_model.classes_
    )

    real_index = classes.index(
        0
    )

    fake_index = classes.index(
        1
    )

    real_probability = float(
        probabilities[
            real_index
        ]
    )

    fake_probability = float(
        probabilities[
            fake_index
        ]
    )

    # ========================================================
    # TEXT THRESHOLD
    # ========================================================

    if (
        fake_probability
        >= TEXT_FAKE_THRESHOLD
    ):

        label = "FAKE"

    else:

        label = "REAL"

    # ========================================================
    # CONFIDENCE
    # ========================================================

    confidence = (
        fake_probability
        if label == "FAKE"
        else real_probability
    )

    # ========================================================
    # EXPLANATION
    # ========================================================

    if label == "FAKE":

        explanation = (
            "The entered text was "
            "classified as FAKE by the "
            "text-based BERT + XGBoost "
            "detector."
        )

    else:

        explanation = (
            "The entered text was "
            "classified as REAL by the "
            "text-based BERT + XGBoost "
            "detector."
        )

    # ========================================================
    # RESULT
    # ========================================================

    return {

        "detector":
            "TEXT_ONLY",

        "model":
            "BERT + Text XGBoost",

        "label":
            label,

        "fake_probability":
            round(
                fake_probability,
                4
            ),

        "real_probability":
            round(
                real_probability,
                4
            ),

        "confidence":
            round(
                confidence,
                4
            ),

        "threshold":
            TEXT_FAKE_THRESHOLD,

        "input_text":
            text,

        "feature_dimensions": {

            "bert":
                BERT_FEATURES

        },

        "text_feature_dimension":
            BERT_FEATURES,

        "human_readable_explanation":
            explanation

    }


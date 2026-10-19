
import json
import os
import uuid
from pathlib import Path

import cv2
import numpy as np
import shap
import torch

from PIL import Image
from torchvision import models, transforms

from models.xgboost_model import model as xgboost_model


# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_DIR = Path(
    r"C:\Users\Anshul\Desktop\fake_news_detection"
)

EXPLANATION_DIR = (
    PROJECT_DIR
    / "backend"
    / "explanations"
)

EXPLANATION_DIR.mkdir(
    parents=True,
    exist_ok=True
)

DEVICE = torch.device(
    "cuda"
    if torch.cuda.is_available()
    else "cpu"
)

IMAGE_SIZE = 224

MAX_FRAMES = 8

RESNET_FEATURES = 2048

BERT_FEATURES = 768

TOTAL_FEATURES = 2816

TOP_FEATURES = 10


# ============================================================
# LOAD RESNET50 CLASSIFICATION MODEL FOR GRAD-CAM
# ============================================================

print()
print("=" * 70)
print("INITIALIZING GRAD-CAM EXPLAINABILITY MODEL")
print("=" * 70)

gradcam_model = models.resnet50(
    weights=models.ResNet50_Weights.DEFAULT
)

gradcam_model = gradcam_model.to(
    DEVICE
)

gradcam_model.eval()

TARGET_LAYER = gradcam_model.layer4[-1]

print(
    "Grad-CAM target layer:",
    "ResNet50.layer4[-1]"
)

print(
    "Grad-CAM device:",
    DEVICE
)


# ============================================================
# IMAGE TRANSFORM
# ============================================================

gradcam_transform = transforms.Compose([

    transforms.Resize(
        (IMAGE_SIZE, IMAGE_SIZE)
    ),

    transforms.ToTensor(),

    transforms.Normalize(
        mean=[
            0.485,
            0.456,
            0.406
        ],

        std=[
            0.229,
            0.224,
            0.225
        ]
    )

])


# ============================================================
# SHAP EXPLAINER
# ============================================================

print()
print("Initializing SHAP TreeExplainer...")

try:

    shap_explainer = shap.TreeExplainer(
        xgboost_model
    )

    print(
        "SHAP explainer ready."
    )

except Exception as error:

    shap_explainer = None

    print(
        "WARNING: SHAP initialization failed:"
    )

    print(
        repr(error)
    )


# ============================================================
# GRAD-CAM STORAGE
# ============================================================

_gradcam_activations = None
_gradcam_gradients = None


# ============================================================
# GRAD-CAM FORWARD HOOK
# ============================================================

def _forward_hook(
    module,
    inputs,
    output
):

    global _gradcam_activations

    _gradcam_activations = output


# ============================================================
# GRAD-CAM BACKWARD HOOK
# ============================================================

def _backward_hook(
    module,
    grad_input,
    grad_output
):

    global _gradcam_gradients

    _gradcam_gradients = grad_output[0]


# ============================================================
# REGISTER GRAD-CAM HOOKS
# ============================================================

forward_handle = TARGET_LAYER.register_forward_hook(
    _forward_hook
)

backward_handle = TARGET_LAYER.register_full_backward_hook(
    _backward_hook
)


# ============================================================
# FRAME SAMPLING
# ============================================================

def _get_frame_indices(
    video_path: str
):

    capture = cv2.VideoCapture(
        video_path
    )

    if not capture.isOpened():

        raise RuntimeError(
            f"Could not open video for Grad-CAM: "
            f"{video_path}"
        )

    total_frames = int(
        capture.get(
            cv2.CAP_PROP_FRAME_COUNT
        )
    )

    capture.release()

    if total_frames <= 0:

        raise RuntimeError(
            "Video contains no readable frames."
        )

    count = min(
        MAX_FRAMES,
        total_frames
    )

    return np.linspace(
        0,
        total_frames - 1,
        count,
        dtype=int
    )


# ============================================================
# GENERATE GRAD-CAM FOR ONE FRAME
# ============================================================

def _generate_gradcam(
    image_pil: Image.Image
):

    global _gradcam_activations
    global _gradcam_gradients

    _gradcam_activations = None
    _gradcam_gradients = None

    tensor = gradcam_transform(
        image_pil
    ).unsqueeze(
        0
    ).to(
        DEVICE
    )

    tensor.requires_grad_(True)

    output = gradcam_model(
        tensor
    )

    target_index = int(
        torch.argmax(
            output,
            dim=1
        ).item()
    )

    target_score = output[
        0,
        target_index
    ]

    gradcam_model.zero_grad(
        set_to_none=True
    )

    target_score.backward()

    if _gradcam_activations is None:

        raise RuntimeError(
            "Grad-CAM activations were not captured."
        )

    if _gradcam_gradients is None:

        raise RuntimeError(
            "Grad-CAM gradients were not captured."
        )

    channel_weights = (
        _gradcam_gradients.mean(
            dim=(2, 3),
            keepdim=True
        )
    )

    cam = (
        channel_weights
        *
        _gradcam_activations
    ).sum(
        dim=1
    )

    cam = torch.relu(
        cam
    )

    cam = cam[
        0
    ]

    cam = (
        cam
        .detach()
        .cpu()
        .numpy()
    )

    cam_min = float(
        np.min(cam)
    )

    cam_max = float(
        np.max(cam)
    )

    if (
        cam_max - cam_min
        >
        1e-8
    ):

        cam = (
            cam - cam_min
        ) / (
            cam_max - cam_min
        )

    else:

        cam = np.zeros_like(
            cam
        )

    cam = cv2.resize(
        cam,
        (
            IMAGE_SIZE,
            IMAGE_SIZE
        ),
        interpolation=cv2.INTER_LINEAR
    )

    return (
        cam,
        target_index,
        float(
            target_score
            .detach()
            .cpu()
            .item()
        )
    )


# ============================================================
# CREATE GRAD-CAM OUTPUT
# ============================================================

def generate_gradcam_explanations(
    video_path: str,
    job_id: str
):

    output_dir = (
        EXPLANATION_DIR
        / job_id
        / "gradcam"
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    frame_indices = _get_frame_indices(
        video_path
    )

    capture = cv2.VideoCapture(
        video_path
    )

    if not capture.isOpened():

        raise RuntimeError(
            "Could not open uploaded video "
            "for Grad-CAM."
        )

    results = []

    for frame_number, index in enumerate(
        frame_indices,
        start=1
    ):

        capture.set(
            cv2.CAP_PROP_POS_FRAMES,
            int(index)
        )

        success, frame = capture.read()

        if not success:

            continue

        frame_rgb = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2RGB
        )

        original_image = Image.fromarray(
            frame_rgb
        ).convert(
            "RGB"
        )

        (
            cam,
            target_index,
            target_score
        ) = _generate_gradcam(
            original_image
        )

        original = np.asarray(
            original_image
        )

        original = cv2.resize(
            original,
            (
                IMAGE_SIZE,
                IMAGE_SIZE
            )
        )

        heatmap = np.uint8(
            255 * cam
        )

        heatmap = cv2.applyColorMap(
            heatmap,
            cv2.COLORMAP_JET
        )

        heatmap = cv2.cvtColor(
            heatmap,
            cv2.COLOR_BGR2RGB
        )

        overlay = cv2.addWeighted(
            original,
            0.55,
            heatmap,
            0.45,
            0
        )

        overlay_filename = (
            f"frame_{frame_number:02d}_gradcam.jpg"
        )

        heatmap_filename = (
            f"frame_{frame_number:02d}_heatmap.jpg"
        )

        original_filename = (
            f"frame_{frame_number:02d}_original.jpg"
        )

        overlay_path = (
            output_dir
            / overlay_filename
        )

        heatmap_path = (
            output_dir
            / heatmap_filename
        )

        original_path = (
            output_dir
            / original_filename
        )

        cv2.imwrite(
            str(overlay_path),
            cv2.cvtColor(
                overlay,
                cv2.COLOR_RGB2BGR
            )
        )

        cv2.imwrite(
            str(heatmap_path),
            cv2.cvtColor(
                heatmap,
                cv2.COLOR_RGB2BGR
            )
        )

        cv2.imwrite(
            str(original_path),
            cv2.cvtColor(
                original,
                cv2.COLOR_RGB2BGR
            )
        )

        results.append({

            "frame_number":
                frame_number,

            "source_frame_index":
                int(index),

            "target_index":
                target_index,

            "target_score":
                target_score,

            "overlay_url":
                f"/explanations/"
                f"{job_id}/gradcam/"
                f"{overlay_filename}",

            "heatmap_url":
                f"/explanations/"
                f"{job_id}/gradcam/"
                f"{heatmap_filename}",

            "original_url":
                f"/explanations/"
                f"{job_id}/gradcam/"
                f"{original_filename}"

        })

    capture.release()

    if not results:

        raise RuntimeError(
            "No Grad-CAM frames were generated."
        )

    average_score = float(
        np.mean([
            item["target_score"]
            for item in results
        ])
    )

    return {

        "available":
            True,

        "method":
            "Grad-CAM",

        "target_layer":
            "ResNet50.layer4[-1]",

        "frames_processed":
            len(results),

        "average_target_score":
            average_score,

        "frames":
            results

    }


# ============================================================
# NORMALIZE SHAP OUTPUT
# ============================================================

def _normalize_shap_values(
    raw_shap_values
):

    # --------------------------------------------------------
    # Older SHAP versions:
    # [class_0_values, class_1_values]
    # --------------------------------------------------------

    if isinstance(
        raw_shap_values,
        list
    ):

        if len(raw_shap_values) > 1:

            raw_shap_values = raw_shap_values[1]

        elif len(raw_shap_values) == 1:

            raw_shap_values = raw_shap_values[0]

        else:

            raise RuntimeError(
                "SHAP returned an empty list."
            )

    # --------------------------------------------------------
    # Newer SHAP Explanation object
    # --------------------------------------------------------

    if hasattr(
        raw_shap_values,
        "values"
    ):

        raw_shap_values = (
            raw_shap_values.values
        )

    shap_values = np.asarray(
        raw_shap_values
    )

    # --------------------------------------------------------
    # Handle possible class dimension
    # --------------------------------------------------------

    if shap_values.ndim == 3:

        # Shape:
        # (samples, features, classes)

        if (
            shap_values.shape[-1] == 2
        ):

            shap_values = (
                shap_values[:, :, 1]
            )

        # Shape:
        # (samples, classes, features)

        elif (
            shap_values.shape[1] == 2
        ):

            shap_values = (
                shap_values[:, 1, :]
            )

        else:

            raise RuntimeError(
                "Unexpected 3D SHAP shape: "
                f"{shap_values.shape}"
            )

    # --------------------------------------------------------
    # Final validation
    # --------------------------------------------------------

    if shap_values.ndim != 2:

        raise RuntimeError(
            "Unexpected SHAP dimensions: "
            f"{shap_values.shape}"
        )

    if shap_values.shape[1] != TOTAL_FEATURES:

        raise RuntimeError(
            "Unexpected SHAP feature dimension: "
            f"{shap_values.shape[1]}. "
            f"Expected {TOTAL_FEATURES}."
        )

    return shap_values


# ============================================================
# SHAP FEATURE NAMES
# ============================================================

def _get_feature_names():

    feature_names = []

    for i in range(
        RESNET_FEATURES
    ):

        feature_names.append(
            f"ResNet50_Feature_{i + 1}"
        )

    for i in range(
        BERT_FEATURES
    ):

        feature_names.append(
            f"BERT_Feature_{i + 1}"
        )

    return feature_names


# ============================================================
# SHAP EXPLANATION
# ============================================================

def generate_shap_explanation(
    fused_features,
    job_id: str
):

    # --------------------------------------------------------
    # Validate SHAP
    # --------------------------------------------------------

    if shap_explainer is None:

        raise RuntimeError(
            "SHAP TreeExplainer is not available."
        )

    # --------------------------------------------------------
    # Convert features
    # --------------------------------------------------------

    features = np.asarray(
        fused_features,
        dtype=np.float32
    ).reshape(
        1,
        -1
    )

    print(
        "[SHAP] Input shape:",
        features.shape
    )

    # --------------------------------------------------------
    # Validate 2816-dimensional fusion
    # --------------------------------------------------------

    if features.shape[1] != TOTAL_FEATURES:

        raise ValueError(
            "SHAP received invalid feature dimension: "
            f"{features.shape[1]}. "
            f"Expected {TOTAL_FEATURES}."
        )

    # --------------------------------------------------------
    # Calculate SHAP
    # --------------------------------------------------------

    try:

        raw_shap_values = (
            shap_explainer.shap_values(
                features
            )
        )

    except Exception as error:

        print(
            "[SHAP] Calculation failed:"
        )

        print(
            repr(error)
        )

        raise RuntimeError(
            "SHAP calculation failed: "
            f"{error}"
        ) from error

    # --------------------------------------------------------
    # Normalize SHAP output
    # --------------------------------------------------------

    shap_values = _normalize_shap_values(
        raw_shap_values
    )

    print(
        "[SHAP] Output shape:",
        shap_values.shape
    )

    values = shap_values[0]

    # --------------------------------------------------------
    # Feature names
    # --------------------------------------------------------

    feature_names = _get_feature_names()

    # --------------------------------------------------------
    # Absolute SHAP importance
    # --------------------------------------------------------

    absolute_values = np.abs(
        values
    )

    # --------------------------------------------------------
    # Top 10 features
    # --------------------------------------------------------

    top_indices = np.argsort(
        absolute_values
    )[::-1][
        :TOP_FEATURES
    ]

    top_features = []

    for rank, index in enumerate(
        top_indices,
        start=1
    ):

        index = int(index)

        contribution = float(
            values[index]
        )

        absolute_shap = float(
            absolute_values[index]
        )

        if contribution > 0:

            direction = "FAKE"

        elif contribution < 0:

            direction = "REAL"

        else:

            direction = "NEUTRAL"

        if index < RESNET_FEATURES:

            modality = "ResNet50"

        else:

            modality = "BERT"

        top_features.append({

            "rank":
                rank,

            "feature":
                feature_names[index],

            "feature_name":
                feature_names[index],

            "feature_index":
                index,

            "modality":
                modality,

            "shap_value":
                contribution,

            "absolute_shap":
                absolute_shap,

            "absolute_shap_value":
                absolute_shap,

            "direction":
                direction

        })

    # --------------------------------------------------------
    # Modality-level SHAP
    #
    # Sum of absolute SHAP values is used here because the
    # modalities have different feature counts.
    # --------------------------------------------------------

    visual_values = values[
        :RESNET_FEATURES
    ]

    text_values = values[
        RESNET_FEATURES:
    ]

    visual_absolute_importance = float(
        np.sum(
            np.abs(
                visual_values
            )
        )
    )

    text_absolute_importance = float(
        np.sum(
            np.abs(
                text_values
            )
        )
    )

    total_importance = (
        visual_absolute_importance
        +
        text_absolute_importance
    )

    if total_importance > 0:

        visual_percentage = float(
            (
                visual_absolute_importance
                /
                total_importance
            )
            * 100
        )

        text_percentage = float(
            (
                text_absolute_importance
                /
                total_importance
            )
            * 100
        )

    else:

        visual_percentage = 0.0

        text_percentage = 0.0

    if (
        visual_absolute_importance
        >
        text_absolute_importance
    ):

        dominant_modality = "ResNet50"

    elif (
        text_absolute_importance
        >
        visual_absolute_importance
    ):

        dominant_modality = "BERT"

    else:

        dominant_modality = "Balanced"

    # --------------------------------------------------------
    # Output directory
    # --------------------------------------------------------

    output_dir = (
        EXPLANATION_DIR
        / job_id
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    # --------------------------------------------------------
    # JSON path
    # --------------------------------------------------------

    json_path = (
        output_dir
        / "shap_explanation.json"
    )

    # --------------------------------------------------------
    # SHAP result
    # --------------------------------------------------------

    shap_result = {

        "available":
            True,

        "method":
            "SHAP TreeExplainer",

        "feature_dimension":
            TOTAL_FEATURES,

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
            visual_absolute_importance,

        "text_absolute_importance":
            text_absolute_importance,

        "visual_percentage":
            visual_percentage,

        "text_percentage":
            text_percentage,

        # Compatibility with older backend code
        "visual_contribution_percent":
            visual_percentage,

        "text_contribution_percent":
            text_percentage,

        "dominant_modality":
            dominant_modality,

        "top_features":
            top_features

    }

    # --------------------------------------------------------
    # Save SHAP JSON
    # --------------------------------------------------------

    with open(
        json_path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            shap_result,
            file,
            indent=4
        )

    # --------------------------------------------------------
    # Frontend URL
    # --------------------------------------------------------

    shap_result[
        "json_url"
    ] = (
        f"/explanations/"
        f"{job_id}/"
        f"shap_explanation.json"
    )

    print(
        "[SHAP] Complete."
    )

    print(
        "[SHAP] Visual contribution:",
        round(
            visual_percentage,
            2
        ),
        "%"
    )

    print(
        "[SHAP] Text contribution:",
        round(
            text_percentage,
            2
        ),
        "%"
    )

    print(
        "[SHAP] Dominant modality:",
        dominant_modality
    )

    print(
        "[SHAP] Top features:",
        len(top_features)
    )

    return shap_result


# ============================================================
# COMPLETE LIVE EXPLANATION PIPELINE
# ============================================================

def generate_explanations(
    video_path: str,
    fused_features
):

    job_id = uuid.uuid4().hex

    print()
    print("=" * 70)
    print("GENERATING LIVE EXPLANATIONS")
    print("=" * 70)

    print(
        "Explanation ID:",
        job_id
    )

    # ========================================================
    # SHAP
    # ========================================================

    print()
    print("Generating SHAP...")

    try:

        shap_result = (
            generate_shap_explanation(
                fused_features,
                job_id
            )
        )

        print(
            "SHAP complete."
        )

    except Exception as error:

        print(
            "[SHAP] ERROR:",
            repr(error)
        )

        shap_result = {

            "available":
                False,

            "method":
                "SHAP TreeExplainer",

            "feature_dimension":
                TOTAL_FEATURES,

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
                str(error)

        }

    # ========================================================
    # GRAD-CAM
    # ========================================================

    print()
    print("Generating Grad-CAM...")

    try:

        gradcam_result = (
            generate_gradcam_explanations(
                video_path,
                job_id
            )
        )

        print(
            "Grad-CAM complete."
        )

    except Exception as error:

        print(
            "[Grad-CAM] ERROR:",
            repr(error)
        )

        gradcam_result = {

            "available":
                False,

            "method":
                "Grad-CAM",

            "target_layer":
                "ResNet50.layer4[-1]",

            "frames_processed":
                0,

            "frames":
                [],

            "error":
                str(error)

        }

    # ========================================================
    # COMPLETE RESULT
    # ========================================================

    print()
    print("=" * 70)
    print("LIVE EXPLANATIONS COMPLETE")
    print("=" * 70)

    print(
        "SHAP available:",
        shap_result.get(
            "available",
            False
        )
    )

    print(
        "Grad-CAM available:",
        gradcam_result.get(
            "available",
            False
        )
    )

    return {

        "explanation_id":
            job_id,

        "shap":
            shap_result,

        "gradcam":
            gradcam_result

    }


"""
TruthLens Grad-CAM
------------------
Generates visual Grad-CAM heatmaps and overlays for sampled video frames.

Compatibility:
    generate_gradcam(video_path, output_dir, max_frames=8)

Returns:
    {
        "available": bool,
        "target_layer": str,
        "frames_processed": int,
        "requested_frames": int,
        "average_target_score": float,
        "frames": [
            {
                "frame_number": int,
                "video_frame_index": int,
                "target_class_index": int,
                "target_probability": float,
                "target_score": float,
                "original_url": str,
                "overlay_url": str,
                "heatmap_url": str
            }
        ]
    }

Note:
    This standalone ResNet50 Grad-CAM explains the selected ImageNet class
    predicted by the ResNet50 backbone. It does not directly explain the
    downstream XGBoost REAL/FAKE probability.
"""

import os
import threading
import traceback

import cv2
import numpy as np
import torch
from PIL import Image
from torchvision import models, transforms


# ============================================================
# DEVICE AND MODEL
# ============================================================

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"[Grad-CAM] Device: {DEVICE}")

MODEL = models.resnet50(weights=models.ResNet50_Weights.DEFAULT)
MODEL = MODEL.to(DEVICE)
MODEL.eval()

TARGET_LAYER = MODEL.layer4[-1]

# Grad-CAM state is shared by the registered forward hook.
# A lock prevents concurrent requests from mixing hook state.
_GRADCAM_LOCK = threading.RLock()
activations = None
gradients = None


# ============================================================
# HOOKS
# ============================================================

def _capture_gradient(gradient):
    """Capture the gradient flowing back through the target-layer output."""
    global gradients
    gradients = gradient.detach()


def _forward_hook(module, inputs, output):
    """
    Save target-layer activations and register a tensor-level gradient hook.

    Registering a hook directly on the output tensor avoids relying on a
    module full-backward hook, which can be fragile with in-place operations
    in torchvision ResNet blocks.
    """
    global activations

    activations = output.detach()

    if output.requires_grad:
        output.register_hook(_capture_gradient)


# Register the forward hook once when the module is imported.
TARGET_LAYER.register_forward_hook(_forward_hook)


# ============================================================
# TRANSFORM
# ============================================================

TRANSFORM = transforms.Compose(
    [
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225],
        ),
    ]
)


# ============================================================
# SINGLE-FRAME GRAD-CAM
# ============================================================

def generate_single_gradcam(frame):
    """
    Generate a Grad-CAM heatmap for one OpenCV BGR frame.

    Returns:
        heatmap, overlay, target_score, target_probability, target_index
    """
    global activations, gradients

    activations = None
    gradients = None

    if frame is None or not isinstance(frame, np.ndarray) or frame.size == 0:
        raise ValueError("Received an empty or invalid frame.")

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    pil_image = Image.fromarray(rgb_frame)

    input_tensor = TRANSFORM(pil_image).unsqueeze(0).to(DEVICE)

    MODEL.zero_grad(set_to_none=True)

    # Explicitly enable gradients even if the caller uses inference_mode or
    # no_grad around its prediction pipeline.
    with torch.enable_grad():
        output = MODEL(input_tensor)

        probabilities = torch.softmax(output, dim=1)
        target_index = int(torch.argmax(probabilities, dim=1).item())

        target_probability = probabilities[0, target_index]
        target_score = output[0, target_index]

        target_score.backward()

    if activations is None:
        raise RuntimeError("Grad-CAM activations were not captured.")

    if gradients is None:
        raise RuntimeError(
            "Grad-CAM gradients were not captured. "
            "Check that gradient calculation is enabled."
        )

    if activations.ndim != 4:
        raise RuntimeError(f"Unexpected activation shape: {activations.shape}")

    if gradients.ndim != 4:
        raise RuntimeError(f"Unexpected gradient shape: {gradients.shape}")

    # Global-average-pool gradients to obtain channel weights.
    weights = torch.mean(gradients, dim=(2, 3), keepdim=True)

    # Weighted sum of feature maps, followed by ReLU.
    cam = torch.sum(weights * activations, dim=1)
    cam = torch.relu(cam).squeeze(0).detach().cpu().numpy()

    if cam.size == 0:
        raise RuntimeError("Grad-CAM produced an empty activation map.")

    cam_min = float(np.min(cam))
    cam_max = float(np.max(cam))
    cam = cam - cam_min

    if cam_max > cam_min:
        cam = cam / (cam_max - cam_min)
    else:
        # A flat map is valid computationally, but contains no localization.
        cam = np.zeros_like(cam, dtype=np.float32)

    cam = cv2.resize(
        cam,
        (frame.shape[1], frame.shape[0]),
        interpolation=cv2.INTER_LINEAR,
    )

    heatmap = np.uint8(255.0 * cam)
    heatmap = cv2.applyColorMap(heatmap, cv2.COLORMAP_JET)

    overlay = cv2.addWeighted(frame, 0.60, heatmap, 0.40, 0)

    score_value = float(target_score.detach().cpu().item())
    probability_value = float(target_probability.detach().cpu().item())

    MODEL.zero_grad(set_to_none=True)

    return (
        heatmap,
        overlay,
        score_value,
        probability_value,
        target_index,
    )


# ============================================================
# VIDEO GRAD-CAM
# ============================================================

def generate_gradcam(video_path, output_dir, max_frames=8):
    """
    Generate Grad-CAM outputs for up to max_frames sampled from a video.

    The returned URL structure is kept compatible with the existing
    TruthLens backend response format.
    """
    if not video_path:
        raise ValueError("Video path is empty.")

    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video not found: {video_path}")

    if int(max_frames) < 1:
        raise ValueError("max_frames must be at least 1.")

    os.makedirs(output_dir, exist_ok=True)

    video_name = os.path.splitext(os.path.basename(video_path))[0]
    safe_video_name = "".join(
        c if c.isalnum() or c in "_-" else "_" for c in video_name
    )

    video_output_dir = os.path.join(output_dir, safe_video_name)
    os.makedirs(video_output_dir, exist_ok=True)

    print("[Grad-CAM] Output directory:", video_output_dir)

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video: {video_path}")

    try:
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total_frames <= 0:
            raise RuntimeError("Video contains no readable frames.")

        number_of_frames = min(int(max_frames), total_frames)
        frame_indices = np.linspace(
            0,
            total_frames - 1,
            number_of_frames,
            dtype=int,
        )

        print("[Grad-CAM] Total video frames:", total_frames)
        print("[Grad-CAM] Processing", len(frame_indices), "frames.")

        results = []
        scores = []

        # The model and hook state are shared; serialize this section to
        # avoid one request overwriting another request's activations/grads.
        with _GRADCAM_LOCK:
            for frame_number, frame_index in enumerate(frame_indices, start=1):
                print(
                    f"[Grad-CAM] Frame {frame_number}/{len(frame_indices)} "
                    f"(video frame {frame_index})"
                )

                cap.set(cv2.CAP_PROP_POS_FRAMES, int(frame_index))
                success, frame = cap.read()

                if not success or frame is None or frame.size == 0:
                    print(f"[Grad-CAM] Could not read frame {frame_index}")
                    continue

                try:
                    (
                        heatmap,
                        overlay,
                        score,
                        probability,
                        target_index,
                    ) = generate_single_gradcam(frame)
                except Exception as exc:
                    print(
                        f"[Grad-CAM] Frame {frame_number} failed: {exc!r}"
                    )
                    traceback.print_exc()
                    continue

                original_filename = f"frame_{frame_number:02d}_original.jpg"
                overlay_filename = f"frame_{frame_number:02d}_overlay.jpg"
                heatmap_filename = f"frame_{frame_number:02d}_heatmap.jpg"

                original_path = os.path.join(
                    video_output_dir, original_filename
                )
                overlay_path = os.path.join(video_output_dir, overlay_filename)
                heatmap_path = os.path.join(video_output_dir, heatmap_filename)

                original_saved = cv2.imwrite(original_path, frame)
                overlay_saved = cv2.imwrite(overlay_path, overlay)
                heatmap_saved = cv2.imwrite(heatmap_path, heatmap)

                if not original_saved:
                    print("[Grad-CAM] Failed to save:", original_path)
                if not overlay_saved:
                    print("[Grad-CAM] Failed to save:", overlay_path)
                if not heatmap_saved:
                    print("[Grad-CAM] Failed to save:", heatmap_path)

                # An overlay is the minimum required artifact for a usable
                # explanation frame.
                if not overlay_saved:
                    continue

                scores.append(score)

                base_url = f"/gradcam/{safe_video_name}"

                results.append(
                    {
                        "frame_number": frame_number,
                        "video_frame_index": int(frame_index),
                        "target_class_index": int(target_index),
                        "target_probability": round(probability, 4),
                        "target_score": round(score, 4),
                        "original_url": f"{base_url}/{original_filename}",
                        "overlay_url": f"{base_url}/{overlay_filename}",
                        "heatmap_url": f"{base_url}/{heatmap_filename}",
                    }
                )
    finally:
        cap.release()
        MODEL.zero_grad(set_to_none=True)

    average_score = float(np.mean(scores)) if scores else 0.0

    result = {
        "available": len(results) > 0,
        "target_layer": "ResNet50.layer4[-1]",
        "frames_processed": len(results),
        "requested_frames": len(frame_indices),
        "average_target_score": round(average_score, 4),
        "frames": results,
    }

    print("[Grad-CAM] Complete.")
    print("[Grad-CAM] Frames generated:", len(results))
    print("[Grad-CAM] Available:", result["available"])

    for item in results:
        print("[Grad-CAM] Overlay:", item["overlay_url"])
        print("[Grad-CAM] Heatmap:", item["heatmap_url"])

    return result

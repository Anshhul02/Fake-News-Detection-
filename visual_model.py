import cv2
import numpy as np
import torch
import torch.nn as nn
from torchvision import models, transforms


# ============================================================
# DEVICE
# ============================================================

DEVICE = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)

print(
    f"Loading ResNet50 on {DEVICE}..."
)


# ============================================================
# RESNET50
# ============================================================

_resnet = models.resnet50(
    weights=models.ResNet50_Weights.DEFAULT
)

# Remove final classification layer
_resnet.fc = nn.Identity()

_resnet = _resnet.to(
    DEVICE
)

_resnet.eval()


# ============================================================
# IMAGE TRANSFORMATION
# ============================================================

_transform = transforms.Compose([

    transforms.ToPILImage(),

    transforms.Resize(
        (224, 224)
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
# VISUAL FEATURE EXTRACTION
# ============================================================

def extract_visual_features(
    video_path: str,
    max_frames: int = 8
):

    print(
        f"Extracting visual features from:\n"
        f"{video_path}"
    )

    capture = cv2.VideoCapture(
        video_path
    )

    if not capture.isOpened():

        raise RuntimeError(
            f"Could not open video:\n"
            f"{video_path}"
        )

    total_frames = int(
        capture.get(
            cv2.CAP_PROP_FRAME_COUNT
        )
    )

    if total_frames <= 0:

        capture.release()

        raise RuntimeError(
            "Video contains no readable frames."
        )

    frame_count = min(
        max_frames,
        total_frames
    )

    frame_indices = np.linspace(
        0,
        total_frames - 1,
        frame_count,
        dtype=int
    )

    frame_features = []

    # ========================================================
    # PROCESS FRAMES
    # ========================================================

    with torch.no_grad():

        for index in frame_indices:

            capture.set(
                cv2.CAP_PROP_POS_FRAMES,
                int(index)
            )

            success, frame = capture.read()

            if not success:

                print(
                    f"Warning: could not read "
                    f"frame {index}"
                )

                continue

            # BGR -> RGB
            frame = cv2.cvtColor(
                frame,
                cv2.COLOR_BGR2RGB
            )

            tensor = _transform(
                frame
            )

            tensor = tensor.unsqueeze(
                0
            )

            tensor = tensor.to(
                DEVICE
            )

            feature = _resnet(
                tensor
            )

            # (1, 2048) -> (2048,)
            feature = (
                feature
                .squeeze(0)
                .cpu()
                .numpy()
                .astype("float32")
            )

            frame_features.append(
                feature
            )

    capture.release()

    if not frame_features:

        raise RuntimeError(
            "No usable frames were extracted."
        )

    frame_features = np.asarray(
        frame_features,
        dtype=np.float32
    )

    # ========================================================
    # TEMPORAL AVERAGING
    # ========================================================

    video_features = np.mean(
        frame_features,
        axis=0
    )

    # Ensure exactly (2048,)
    video_features = np.asarray(
        video_features,
        dtype=np.float32
    ).reshape(-1)

    if video_features.shape[0] != 2048:

        raise RuntimeError(
            f"Unexpected ResNet50 feature dimension: "
            f"{video_features.shape}"
        )

    print(
        "ResNet50 feature dimension:",
        len(video_features)
    )

    return video_features


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print(
        "\nvisual_model.py loaded successfully."
    )

    print(
        "Function available:"
    )

    print(
        "extract_visual_features()"
    )
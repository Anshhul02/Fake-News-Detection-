import numpy as np


def fuse_features(
    visual_features,
    text_features
):

    visual_features = np.asarray(
        visual_features
    ).flatten()

    text_features = np.asarray(
        text_features
    ).flatten()

    fused_features = np.concatenate(
        [
            visual_features,
            text_features
        ]
    )

    return fused_features


if __name__ == "__main__":

    visual = np.zeros(2048)

    text = np.zeros(768)

    fused = fuse_features(
        visual,
        text
    )

    print(
        "Visual features:",
        visual.shape
    )

    print(
        "Text features:",
        text.shape
    )

    print(
        "Fused features:",
        fused.shape
    )
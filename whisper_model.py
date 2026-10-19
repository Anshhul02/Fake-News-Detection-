import os
import whisper


# ============================================================
# WHISPER
# ============================================================

print(
    "Loading Whisper model..."
)

WHISPER_MODEL_NAME = "base"

_whisper = whisper.load_model(
    WHISPER_MODEL_NAME
)

print(
    f"Whisper '{WHISPER_MODEL_NAME}' loaded successfully."
)


# ============================================================
# TRANSCRIBE VIDEO
# ============================================================

def transcribe_video(
    video_path: str
) -> str:

    """
    Transcribe video audio using Whisper.

    This function does NOT use:
        actual_label
        predicted_label
        REAL
        FAKE
    """

    if not video_path:

        raise ValueError(
            "Video path is empty."
        )

    if not os.path.exists(
        video_path
    ):

        raise FileNotFoundError(
            f"Video not found:\n"
            f"{video_path}"
        )

    print(
        f"Transcribing video:\n"
        f"{video_path}"
    )

    try:

        result = _whisper.transcribe(
            video_path,
            fp16=False
        )

        transcript = result.get(
            "text",
            ""
        )

        transcript = str(
            transcript
        ).strip()

        if not transcript:

            raise RuntimeError(
                "Whisper produced an empty transcript."
            )

        print(
            "Transcript successfully extracted."
        )

        return transcript

    except Exception as e:

        raise RuntimeError(
            f"Whisper transcription failed: {e}"
        ) from e


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print(
        "whisper_model.py loaded successfully."
    )

    print(
        "Function available:"
    )

    print(
        "transcribe_video()"
    )
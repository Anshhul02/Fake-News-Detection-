import whisper


_whisper_model = None


def load_whisper():

    global _whisper_model

    if _whisper_model is None:

        print("Loading Whisper model...")

        _whisper_model = whisper.load_model(
            "base"
        )

        print("Whisper loaded successfully.")

    return _whisper_model


def transcribe_audio(video_path: str):

    model = load_whisper()

    print(
        "Transcribing video..."
    )

    result = model.transcribe(
        video_path
    )

    transcript = result.get(
        "text",
        ""
    )

    transcript = transcript.strip()

    print(
        f"Transcript length: "
        f"{len(transcript)} characters"
    )

    return transcript
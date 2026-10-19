import subprocess
import os


def extract_audio(video_path, audio_path):
    """
    Extract audio from a video and save it as WAV.
    """

    if not os.path.exists(video_path):
        raise FileNotFoundError(
            f"Video not found: {video_path}"
        )

    os.makedirs(
        os.path.dirname(audio_path),
        exist_ok=True
    )

    command = [
        "ffmpeg",
        "-y",
        "-i",
        video_path,
        "-vn",
        "-acodec",
        "pcm_s16le",
        "-ar",
        "16000",
        "-ac",
        "1",
        audio_path
    ]

    subprocess.run(
        command,
        check=True
    )

    print(f"Audio extracted successfully:")
    print(audio_path)


if __name__ == "__main__":

    video_path = "test_video.mp4"

    audio_path = "outputs/audio.wav"

    extract_audio(
        video_path,
        audio_path
    )
import cv2
import os


def extract_frames(video_path, output_dir, frame_interval=30):
    """
    Extract frames from a video.

    video_path:
        Path to input video

    output_dir:
        Directory where extracted frames will be saved

    frame_interval:
        Save one frame every N frames
    """

    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video not found: {video_path}")

    os.makedirs(output_dir, exist_ok=True)

    video = cv2.VideoCapture(video_path)

    if not video.isOpened():
        raise ValueError("Could not open the video.")

    frame_count = 0
    saved_count = 0

    while True:

        success, frame = video.read()

        if not success:
            break

        if frame_count % frame_interval == 0:

            frame_filename = os.path.join(
                output_dir,
                f"frame_{saved_count:05d}.jpg"
            )

            cv2.imwrite(frame_filename, frame)

            saved_count += 1

        frame_count += 1

    video.release()

    print(f"Total frames processed: {frame_count}")
    print(f"Frames extracted: {saved_count}")

    return saved_count


if __name__ == "__main__":

    video_path = "test_video.mp4"
    output_dir = "outputs/frames"

    extract_frames(
        video_path,
        output_dir,
        frame_interval=30
    )
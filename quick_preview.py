"""Generate a quick 10-second preview video of the koi animation without writing intermediate frame files."""
import os
import math
import cv2
import numpy as np
from PIL import Image, ImageDraw
from generate_fish_animation import KoiFish
import config

def render_quick_preview(duration_seconds=10):
    """Render a short preview video directly to MP4 (no frame files needed)."""
    os.makedirs(config.VIDEOS_DIR, exist_ok=True)
    output_path = os.path.join(config.VIDEOS_DIR, "koi_preview.mp4")

    width = config.PROJECTOR_WIDTH
    height = config.PROJECTOR_HEIGHT
    fps = config.ANIMATION_FPS
    total_frames = fps * duration_seconds
    delta_time = 1.0 / fps

    fish_list = [KoiFish(width, height) for _ in range(config.FISH_COUNT)]
    for fish in fish_list:
        fish.set_fish_list(fish_list)

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    print(f"Rendering {duration_seconds}s koi preview ({total_frames} frames)...")

    for frame_index in range(total_frames):
        time_seconds = frame_index / fps

        image = Image.new("RGB", (width, height), "white")
        draw_context = ImageDraw.Draw(image)

        for fish in fish_list:
            fish.update(time_seconds, delta_time)
            fish.draw(draw_context, time_seconds)

        # Convert PIL to OpenCV format (RGB -> BGR)
        frame_array = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        writer.write(frame_array)

        if frame_index % 100 == 0:
            print(f"  {frame_index}/{total_frames}")

    writer.release()
    file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"Done! Preview: {output_path} ({file_size_mb:.1f} MB)")
    return output_path

if __name__ == "__main__":
    render_quick_preview()

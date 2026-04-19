"""Combines corrected frames into an MP4 video using ffmpeg.
Run this after generate_fish_animation.py and apply_keystone_correction.py.
Also supports a one-shot pipeline that does all three steps.
"""
import os
import subprocess
import shutil
import config


def export_frames_to_video(scene_name="fish"):
    """Encode corrected frames into an MP4 video file using ffmpeg."""
    os.makedirs(config.VIDEOS_DIR, exist_ok=True)

    input_pattern = os.path.join(config.CORRECTED_FRAMES_DIR, "frame_%06d.png")
    output_path = os.path.join(config.VIDEOS_DIR, f"{scene_name}.mp4")

    # Check that corrected frames exist
    if not os.path.isdir(config.CORRECTED_FRAMES_DIR):
        print(f"No corrected frames directory found at {config.CORRECTED_FRAMES_DIR}")
        print("Run apply_keystone_correction.py first.")
        return None

    frame_count = len([f for f in os.listdir(config.CORRECTED_FRAMES_DIR) if f.endswith(".png")])
    if frame_count == 0:
        print("No corrected frames found. Run the full pipeline first.")
        return None

    print(f"Exporting {frame_count} frames to video...")
    print(f"  Input pattern: {input_pattern}")
    print(f"  Output: {output_path}")
    print(f"  FPS: {config.ANIMATION_FPS}")
    print(f"  Resolution: {config.PROJECTOR_WIDTH}x{config.PROJECTOR_HEIGHT}")

    # ffmpeg command: encode frames to H.264 MP4
    # -y: overwrite output
    # -framerate: input frame rate
    # -i: input pattern
    # -c:v libx264: H.264 codec (widely supported on Pi)
    # -pix_fmt yuv420p: pixel format for broad compatibility
    # -preset medium: balance between speed and compression
    # -crf 18: high quality (lower = better, 18 is visually lossless)
    ffmpeg_command = [
        "ffmpeg",
        "-y",
        "-framerate", str(config.ANIMATION_FPS),
        "-i", input_pattern,
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-preset", "medium",
        "-crf", "18",
        "-vf", f"scale={config.PROJECTOR_WIDTH}:{config.PROJECTOR_HEIGHT}",
        output_path,
    ]

    print(f"  Command: {' '.join(ffmpeg_command)}")

    result = subprocess.run(ffmpeg_command, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"ffmpeg failed with return code {result.returncode}")
        print(f"stderr: {result.stderr[-500:]}")
        return None

    file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"Done! Video saved to {output_path} ({file_size_mb:.1f} MB)")
    return output_path


def run_full_pipeline(scene_name="fish"):
    """Run the complete pipeline: generate frames → keystone correct → export video."""
    print("=" * 60)
    print("CAT PROJECT - Full Video Pipeline")
    print("=" * 60)

    # Step 1: Generate animation frames
    print("\n--- Step 1: Generating fish animation frames ---")
    from generate_fish_animation import generate_all_frames
    generate_all_frames()

    # Step 2: Apply keystone correction
    print("\n--- Step 2: Applying keystone correction ---")
    from apply_keystone_correction import correct_all_frames
    correct_all_frames()

    # Step 3: Export to video
    print("\n--- Step 3: Exporting to MP4 video ---")
    video_path = export_frames_to_video(scene_name)

    if video_path:
        print("\n" + "=" * 60)
        print(f"Pipeline complete! Video ready at: {video_path}")
        print(f"Copy this to your Pi: scp {video_path} pi@<PI_IP>:~/cat_project/videos/")
        print("=" * 60)

    return video_path


def cleanup_frames():
    """Remove intermediate frame directories to save disk space."""
    for directory in [config.FRAMES_DIR, config.CORRECTED_FRAMES_DIR]:
        if os.path.isdir(directory):
            frame_count = len(os.listdir(directory))
            shutil.rmtree(directory)
            print(f"Removed {directory} ({frame_count} files)")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--full":
        run_full_pipeline()
    elif len(sys.argv) > 1 and sys.argv[1] == "--cleanup":
        cleanup_frames()
    else:
        export_frames_to_video()

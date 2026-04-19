"""Controls video playback on the Raspberry Pi using VLC.
This module is imported by whatsapp_bot.py to start/stop/switch video scenes.
VLC runs in a subprocess, fullscreen, looping the current video.
"""
import os
import subprocess
import signal
import logging

log = logging.getLogger("playback")

# Track the current VLC process and state
_current_process = None
_current_scene = None
_is_playing = False


def get_video_path(scene_name):
    """Resolve the full path to a video file for a given scene name."""
    # Check Pi video directory first, then fall back to project assets
    possible_paths = [
        os.path.expanduser(f"~/cat_project/videos/{scene_name}.mp4"),
        os.path.join(os.path.dirname(__file__), "assets", "videos", f"{scene_name}.mp4"),
    ]
    for path in possible_paths:
        if os.path.isfile(path):
            return path
    return None


def list_available_scenes():
    """Return a list of available scene names (video files without extension)."""
    scenes = []
    video_directories = [
        os.path.expanduser("~/cat_project/videos"),
        os.path.join(os.path.dirname(__file__), "assets", "videos"),
    ]
    for video_directory in video_directories:
        if os.path.isdir(video_directory):
            for filename in os.listdir(video_directory):
                if filename.endswith(".mp4"):
                    scene_name = filename.replace(".mp4", "")
                    if scene_name not in scenes:
                        scenes.append(scene_name)
    return scenes


def start_playback(scene_name="fish"):
    """Start playing a video scene in fullscreen loop. Stops any current playback first."""
    global _current_process, _current_scene, _is_playing

    video_path = get_video_path(scene_name)
    if video_path is None:
        available = list_available_scenes()
        log.error(f"Video not found for scene '{scene_name}'. Available: {available}")
        return False, f"Scene '{scene_name}' not found. Available: {', '.join(available) or 'none'}"

    # Stop current playback if running
    stop_playback()

    # Launch VLC in fullscreen, looping, no interface
    vlc_command = [
        "cvlc",             # VLC without GUI (command-line only)
        "--fullscreen",
        "--loop",           # Loop the video forever
        "--no-osd",         # No on-screen display
        "--no-audio",       # No audio needed for cat toy
        "--video-on-top",   # Keep video on top
        video_path,
    ]

    log.info(f"Starting playback: {scene_name} ({video_path})")

    try:
        _current_process = subprocess.Popen(
            vlc_command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        _current_scene = scene_name
        _is_playing = True
        return True, f"Playing '{scene_name}'"
    except FileNotFoundError:
        log.error("VLC (cvlc) not found. Install with: sudo apt install vlc")
        return False, "VLC not installed on this Pi"
    except Exception as error:
        log.error(f"Failed to start VLC: {error}")
        return False, f"Playback error: {error}"


def stop_playback():
    """Stop the current video playback."""
    global _current_process, _current_scene, _is_playing

    if _current_process is not None:
        try:
            _current_process.send_signal(signal.SIGTERM)
            _current_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            _current_process.kill()
            _current_process.wait()
        except Exception as error:
            log.error(f"Error stopping VLC: {error}")
            # Force kill as fallback
            try:
                subprocess.run(["killall", "vlc"], capture_output=True)
            except Exception:
                pass

        _current_process = None
        log.info(f"Stopped playback of '{_current_scene}'")

    _is_playing = False
    _current_scene = None
    return True, "Playback stopped"


def get_status():
    """Return current playback status as a human-readable string."""
    if _is_playing and _current_scene:
        # Verify the process is actually still running
        if _current_process and _current_process.poll() is None:
            return f"Playing: {_current_scene}"
        else:
            return "Stopped (process ended unexpectedly)"
    return "Stopped"


def switch_scene(scene_name):
    """Switch to a different scene (stop current, start new)."""
    return start_playback(scene_name)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    import sys

    if len(sys.argv) < 2:
        print("Usage: python playback_controller.py <command> [scene_name]")
        print("Commands: play, stop, status, list")
        print(f"Current status: {get_status()}")
        sys.exit(0)

    command = sys.argv[1].lower()

    if command == "play":
        scene = sys.argv[2] if len(sys.argv) > 2 else "fish"
        success, message = start_playback(scene)
        print(message)
    elif command == "stop":
        success, message = stop_playback()
        print(message)
    elif command == "status":
        print(get_status())
    elif command == "list":
        scenes = list_available_scenes()
        print(f"Available scenes: {', '.join(scenes) or 'none'}")
    else:
        print(f"Unknown command: {command}")

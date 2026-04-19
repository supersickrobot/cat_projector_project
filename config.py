"""Configuration for the Cat Project."""
import os

# --- Projector / Display ---
PROJECTOR_WIDTH = 800
PROJECTOR_HEIGHT = 480
PROJECTOR_ASPECT_RATIO = PROJECTOR_WIDTH / PROJECTOR_HEIGHT

# --- Projection Geometry ---
# Angle in degrees from horizontal (projector pointing down from shelf)
PROJECTION_ANGLE_DEGREES = 30.0

# --- Animation Settings ---
ANIMATION_FPS = 30
ANIMATION_DURATION_SECONDS = 180  # 3 minute loop
TOTAL_FRAMES = ANIMATION_FPS * ANIMATION_DURATION_SECONDS

# Fish scene settings
FISH_COUNT = 20
FISH_MIN_SPEED = 45   # pixels per second
FISH_MAX_SPEED = 90   # pixels per second
FISH_MIN_SIZE = 40    # pixels (body length)
FISH_MAX_SIZE = 65    # pixels (body length)

# --- Paths ---
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(PROJECT_DIR, "assets")
FRAMES_DIR = os.path.join(ASSETS_DIR, "frames")
CORRECTED_FRAMES_DIR = os.path.join(ASSETS_DIR, "corrected_frames")
VIDEOS_DIR = os.path.join(ASSETS_DIR, "videos")

# On the Pi, videos live here
PI_VIDEOS_DIR = os.path.expanduser("~/cat_project/videos")

# --- Twilio / WhatsApp ---
# Set these via environment variables or edit directly
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID", "YOUR_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN", "YOUR_AUTH_TOKEN")
TWILIO_WHATSAPP_NUMBER = os.environ.get("TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886")  # Twilio sandbox default

# --- Playback ---
# VLC is the default player on Raspberry Pi OS
VLC_PATH = "/usr/bin/vlc"
PLAYBACK_FULLSCREEN = True
PLAYBACK_LOOP = True

# --- Network ---
FLASK_HOST = "0.0.0.0"
FLASK_PORT = 5000

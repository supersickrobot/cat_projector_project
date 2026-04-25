"""Configuration for the Cat Project."""
import os

# --- Projector / Display ---
PROJECTOR_WIDTH = 800
PROJECTOR_HEIGHT = 480
PROJECTOR_ASPECT_RATIO = PROJECTOR_WIDTH / PROJECTOR_HEIGHT

# --- Projection Geometry ---
# Angle in degrees from horizontal (projector pointing down from shelf)
# Calibrated empirically from measured floor widths (84" top / 64" bottom) -> ~25°.
PROJECTION_ANGLE_DEGREES = 25.0
# Approximate vertical field-of-view of the projector lens (degrees). Used to estimate
# how much the top/bottom rays diverge.
PROJECTION_VERTICAL_FOV_DEGREES = 28.0
# If True, flip the keystone correction (top↔bottom). Use this when the projector's
# image is mounted/oriented such that the BOTTOM of the source frame ends up as the
# close (short-throw) edge on the floor instead of the top.
KEYSTONE_INVERT = True
# If set (not None), this value is used directly as the floor width ratio instead of
# computing it from PROJECTION_ANGLE_DEGREES. Handy for iterative empirical tuning:
#   ratio = (measured floor width at FAR/wide edge) / (measured floor width at CLOSE/narrow edge)
# Example: floor measured 84" top, 64" bottom -> 84/64 = 1.3125 if measurements were taken
# with NO correction applied. If taken WITH the current correction in place, multiply by
# (current_far_source_width / current_close_source_width) to back out the physical ratio.
# Setting this to 1.0 produces NO pre-warp (identity transform). Use this if you want
# the natural perspective look — fish near the projector appear small, fish at the far
# edge appear large (depth illusion). Set to None to use angle-based correction.
KEYSTONE_WIDTH_RATIO_OVERRIDE = 1.0




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

# --- Telegram Bot ---
# Get a token from @BotFather on Telegram
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN")

# --- Twilio / WhatsApp (legacy, keeping for reference) ---
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID", "YOUR_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN", "YOUR_AUTH_TOKEN")
TWILIO_WHATSAPP_NUMBER = os.environ.get("TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886")

# --- Playback ---
# VLC is the default player on Raspberry Pi OS
VLC_PATH = "/usr/bin/vlc"
PLAYBACK_FULLSCREEN = True
PLAYBACK_LOOP = True

# --- Network ---
FLASK_HOST = "0.0.0.0"
FLASK_PORT = 5000

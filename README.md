# Cat Projector Project 🐱🐟

A Raspberry Pi-powered cat toy that projects animated fish shadows onto the floor for cats to chase. Uses an RCA RPJ227 projector mounted on a shelf, angled ~30° downward.

## Hardware

- **Projector**: RCA RPJ227 (800×480, HDMI input)
- **Computer**: Raspberry Pi 4 Model B
- **Mount**: Shelf-mounted, pointing down at ~30° angle

## What It Does

Generates looping video of black koi fish shadows swimming on a white background. The fish use a biomechanically accurate locomotion model (based on Tu & Terzopoulos, 1994 "Artificial Fishes") with:

- **Traveling body wave** — sine wave propagates head-to-tail with quadratic amplitude envelope
- **Thrust from tail wag** — speed comes from tail oscillation, fish coast between bursts
- **Body curvature steering** — heading change is derived from body bend × speed (fish can only turn as fast as their body curves)
- **Space-seeking waypoints** — fish naturally spread across the canvas, targeting emptier areas
- **Intermittent burst envelope** — alternating active swimming and coasting phases
- **V-shaped tail fins** — coupled to the body wave

The video includes a 30° keystone pre-correction so it projects flat on the floor despite the angled projector.

## Project Structure

```
cat_project/
├── config.py                    # All tunable parameters
├── generate_fish_animation.py   # Core fish animation engine (KoiFish class)
├── quick_preview.py             # Fast preview render (direct to MP4)
├── apply_keystone_correction.py # 30° perspective pre-warp for angled projection
├── export_video.py              # Full pipeline: render → keystone correct → encode H.264
├── playback_controller.py       # VLC-based fullscreen looping playback for Pi
├── whatsapp_bot.py              # Twilio WhatsApp bot for remote on/off/scene control
├── setup_pi.sh                  # Raspberry Pi deployment script
├── requirements.txt             # Python dependencies
└── assets/
    └── videos/                  # Generated video files
```

## Quick Start (Development on PC)

```bash
# Install dependencies
pip install pillow opencv-python numpy

# Generate a 20-second preview
python -c "from quick_preview import render_quick_preview; render_quick_preview(20)"

# Generate the full 3-minute production video
python -c "from quick_preview import render_quick_preview; render_quick_preview(180)"
```

## Configuration

All parameters are in `config.py`:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `FISH_COUNT` | 20 | Number of fish |
| `FISH_MIN_SPEED` | 45 | Minimum speed (px/s) |
| `FISH_MAX_SPEED` | 90 | Maximum speed (px/s) |
| `FISH_MIN_SIZE` | 40 | Smallest fish (px) |
| `FISH_MAX_SIZE` | 65 | Largest fish (px) |
| `ANIMATION_DURATION_SECONDS` | 180 | Loop length (3 min) |
| `PROJECTION_ANGLE_DEGREES` | 30.0 | Projector tilt angle |

## Raspberry Pi Deployment

```bash
# On the Pi:
chmod +x setup_pi.sh
./setup_pi.sh

# Set Twilio env vars for WhatsApp control:
export TWILIO_ACCOUNT_SID="your_sid"
export TWILIO_AUTH_TOKEN="your_token"
export TWILIO_WHATSAPP_NUMBER="whatsapp:+1234567890"
```

The setup script installs dependencies, copies videos, and creates systemd services for:
- **Auto-start video playback** on boot (fullscreen VLC loop)
- **WhatsApp bot** for remote control

## WhatsApp Commands

Send these messages to the Twilio WhatsApp number:
- `off` — Stop playback
- `fish` — Start/restart fish animation
- `status` — Check if playing

## Export Pipeline (Full Quality)

For Pi-ready H.264 video with keystone correction:

```bash
python export_video.py
```

This renders all frames → applies 30° perspective warp → encodes to compact H.264 MP4.

## License

MIT

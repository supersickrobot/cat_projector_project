# Cat Projector Project 🐱🐟

A phone-controlled cat toy. A projector sits on a shelf and projects realistic swimming fish shadows onto the floor. You turn it on and off from your phone using Telegram — just open the chat and type "on" or "off".

The fish look real: they swim with body waves, coast between tail wag bursts, curve their bodies to steer, and spread naturally across the floor. Built with a Raspberry Pi, a cheap projector, and a free Telegram bot.

## How It Works

1. **Projector on a shelf** — An RCA RPJ227 projector points down at ~30° from a shelf. A Raspberry Pi drives it over HDMI.
2. **Fish animation** — The Pi plays a looping video of 20 black koi fish shadows swimming on a white background. The video has keystone correction baked in so the fish look flat on the floor despite the angled projector.
3. **Phone control** — A Telegram bot runs on the Pi. You text "on" to start the fish, "off" to stop them. No app to install beyond Telegram, no monthly fees, works from anywhere with internet.

## Hardware

- **Projector**: RCA RPJ227 (800×480, HDMI)
- **Computer**: Raspberry Pi 4 Model B
- **Mount**: Shelf-mounted, angled ~30° downward
- **Connection**: HDMI from Pi to projector

## Project Structure

```
cat_project/
├── config.py                    # All tunable parameters
├── generate_fish_animation.py   # Core fish animation engine (KoiFish class)
├── quick_preview.py             # Fast preview render (direct to MP4)
├── apply_keystone_correction.py # 30° perspective pre-warp for angled projection
├── calibration_image.py         # Generate fullscreen alignment grid for projector setup
├── export_video.py              # Full pipeline: render → keystone correct → encode H.264

├── playback_controller.py       # VLC-based fullscreen looping playback for Pi
├── telegram_bot.py              # Telegram bot for remote on/off control
├── setup_pi.sh                  # Raspberry Pi deployment script
├── requirements.txt             # Python dependencies
└── assets/
    └── videos/                  # Generated video files (gitignored)
```

## Quick Start (Generate Videos on PC)

```bash
# Clone the repo
git clone https://github.com/supersickrobot/cat_projector_project.git
cd cat_projector_project

# Install dependencies
pip install pillow opencv-python numpy

# Generate a 20-second preview
python -c "from quick_preview import render_quick_preview; render_quick_preview(20)"

# Generate the full 3-minute production video
python -c "from quick_preview import render_quick_preview; render_quick_preview(180)"
```

## Telegram Bot Setup

The projector is controlled remotely via a free Telegram bot. No monthly costs, no phone number needed, no public URL/ngrok required.

### 1. Create Your Bot (30 seconds)

1. Open **Telegram** on your phone
2. Search for **@BotFather** and start a chat
3. Send `/newbot`
4. Choose a name (e.g. "Cat Projector")
5. Choose a username (e.g. `my_cat_projector_bot` — must end in `bot`)
6. BotFather replies with your **bot token** — copy it

### 2. Run the Bot

```bash
# Set your token as an environment variable (don't commit it!)
export TELEGRAM_BOT_TOKEN="your_token_here"

# Start the bot
python telegram_bot.py
```

### 3. Use It

Open your bot in Telegram and send:

| Message | What it does |
|---------|-------------|
| `on` | Start the fish animation |
| `off` | Stop playback |
| `status` | Check what's playing |
| `help` | Show available commands |

### Security (Optional)

When you first message the bot, it shows your Telegram user ID. To restrict the bot to only your account, add your ID to `ALLOWED_USER_IDS` in `telegram_bot.py`:

```python
ALLOWED_USER_IDS = [123456789]  # your Telegram user ID
```

## Configuration

All animation parameters are in `config.py`:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `FISH_COUNT` | 20 | Number of fish |
| `FISH_MIN_SPEED` | 45 | Minimum speed (px/s) |
| `FISH_MAX_SPEED` | 90 | Maximum speed (px/s) |
| `FISH_MIN_SIZE` | 40 | Smallest fish body length (px) |
| `FISH_MAX_SIZE` | 65 | Largest fish body length (px) |
| `ANIMATION_DURATION_SECONDS` | 180 | Loop length (3 min) |
| `PROJECTION_ANGLE_DEGREES` | 30.0 | Projector tilt from horizontal |
| `PROJECTION_VERTICAL_FOV_DEGREES` | 28.0 | Approximate vertical FOV of the projector lens |
| `KEYSTONE_INVERT` | False | Flip top↔bottom on keystone correction (use if your projector orientation makes the bottom of the source the close edge on the floor) |
| `KEYSTONE_WIDTH_RATIO_OVERRIDE` | None | Bypass the angle math with a measured ratio. Set to `1.0` to disable keystone entirely and get **natural perspective** (fish small near, large far) |

## Calibration

A simple way to align the projector and tune the keystone:

```bash
# Generate a 1920×1080 calibration image with edge arrows + corner markers
python3 calibration_image.py

# Project it fullscreen
vlc --fullscreen --no-osd --intf dummy --image-duration=-1 --loop \
    assets/videos/calibration.png
```

Then measure the projected widths on the floor at the top edge and bottom
edge. The ratio top:bottom tells you the residual perspective distortion;
plug numbers into `PROJECTION_ANGLE_DEGREES` (or `KEYSTONE_WIDTH_RATIO_OVERRIDE`)
and re-render.

For a real-world deployment example with measured numbers, see
[`DEPLOYMENT_NOTES.md`](DEPLOYMENT_NOTES.md).

## Raspberry Pi Deployment


```bash
# On the Pi — clone and set up
git clone https://github.com/supersickrobot/cat_projector_project.git
cd cat_projector_project
chmod +x setup_pi.sh
./setup_pi.sh
```

The setup script:
1. Installs VLC, Python dependencies, and `python-telegram-bot`
2. Copies generated videos to `~/cat_project/videos/`
3. Creates systemd services for auto-start on boot:
   - **Video playback** — fullscreen VLC loop
   - **Telegram bot** — listens for on/off commands

Set your bot token on the Pi:
```bash
# Add to ~/.bashrc or /etc/environment for persistence
export TELEGRAM_BOT_TOKEN="your_token_here"
```

## Export Pipeline (Full Quality for Pi)

For a Pi-ready H.264 video with keystone correction baked in:

```bash
python export_video.py
```

This renders all frames → applies the 30° perspective warp → encodes to a compact H.264 MP4.

## How the Fish Work

The animation is based on the **Tu & Terzopoulos (1994)** "Artificial Fishes" locomotion model:

1. **Body wave**: A sine wave travels from head to tail. Amplitude increases quadratically — the head barely moves, the tail swings wide. This is how real fish swim.

2. **Thrust**: Forward speed comes from tail oscillation. During active wag bursts the fish accelerates; between bursts it coasts and slows (bounded to 45–90 px/s).

3. **Steering**: The body physically curves to turn. The heading change rate equals `body_curvature × speed / body_length`. A slow fish with a curved body turns slowly. A fast fish with the same curve turns faster. The body curvature smoothly tracks a desired turn angle (muscle response lag).

4. **Waypoints**: Each fish picks random target points to swim toward. Candidates are scored by distance from other fish — the emptiest spot wins. This creates natural spreading without hard repulsion.

5. **Burst envelope**: A low-frequency oscillator modulates the tail wag amplitude, creating intermittent swimming — active bursts followed by coasting — which looks much more natural than constant swimming.

## License

MIT

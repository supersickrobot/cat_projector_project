# Cat Projector Project 🐱🐟

A Raspberry Pi-powered cat toy that projects animated fish shadows onto the floor for cats to chase. Uses an RCA RPJ227 projector mounted on a shelf, angled ~30° downward.

## Hardware

- **Projector**: RCA RPJ227 (800×480, HDMI input)
- **Computer**: Raspberry Pi 4 Model B
- **Mount**: Shelf-mounted, pointing down at ~30° angle
- **Connection**: HDMI from Pi to projector

## What It Does

Generates a looping video of black koi fish shadows swimming across a white background. The fish use a biomechanically accurate locomotion model (based on Tu & Terzopoulos, 1994 "Artificial Fishes") with:

- **Traveling body wave** — sine wave propagates head-to-tail with quadratic amplitude envelope
- **Thrust from tail wag** — speed comes from tail oscillation, fish coast between bursts
- **Body curvature steering** — heading change is derived from body bend × speed
- **Space-seeking waypoints** — fish naturally spread across the canvas, targeting emptier areas
- **Intermittent burst envelope** — alternating active swimming and coasting phases
- **V-shaped tail fins** — coupled to the body wave

The video includes a 30° keystone pre-correction so it projects flat on the floor despite the angled projector.

You control it from your phone via a **Telegram bot** — send "on" to start, "off" to stop.

## Project Structure

```
cat_project/
├── config.py                    # All tunable parameters
├── generate_fish_animation.py   # Core fish animation engine (KoiFish class)
├── quick_preview.py             # Fast preview render (direct to MP4)
├── apply_keystone_correction.py # 30° perspective pre-warp for angled projection
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

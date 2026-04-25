# Deployment Notes — Real-World Setup

These are working notes from an actual deployment on an x86 Mini-PC (not a Pi)
running Ubuntu 24.04, with an RCA RPJ227 projector mounted on a shelf and
pointed at the floor at roughly 25° from horizontal.

## Hardware in this build

| Component | Detail |
|---|---|
| Computer | AZW MINI S — x86_64 mini PC, Ubuntu 24.04 LTS |
| Projector | RCA RPJ227 (800×480 native, accepts up to 1080p over HDMI) |
| Network | Wi-Fi (`wlp2s0`) on local LAN |
| Display port | HDMI-2 from the mini PC → HDMI input on the projector |
| Remote control | (planned) Broadlink RM4 Mini IR blaster |

## Calibrated values for this physical setup

Measured floor projection widths with a tape measure:
- Top edge (far from projector): **84"**
- Bottom edge (close to projector): **64"**

Computed projection angle: **~25°** from horizontal (not the README's 30°).

These live in `config.py`:

```python
PROJECTION_ANGLE_DEGREES = 25.0
PROJECTION_VERTICAL_FOV_DEGREES = 28.0
KEYSTONE_INVERT = True
KEYSTONE_WIDTH_RATIO_OVERRIDE = 1.0   # 1.0 = no pre-warp = natural perspective
```

`KEYSTONE_WIDTH_RATIO_OVERRIDE = 1.0` is the most important line. It means:
**we are intentionally NOT applying keystone correction** because we want
fish near the projector to look small and fish at the far edge to look big
(natural depth illusion). The cats love the perspective effect.

If you want a flat rectangular projection (every fish the same physical
size), set `KEYSTONE_WIDTH_RATIO_OVERRIDE = None` and the angle/FOV math
will compute the correct pre-warp.

## Step-by-step deployment that worked

### 1. Clone & install Python deps

```bash
git clone https://github.com/supersickrobot/cat_projector_project.git
cd cat_projector_project
pip install --user --break-system-packages -r requirements.txt
```

### 2. Render the video

```bash
python3 export_video.py --full
python3 export_video.py --cleanup   # drops intermediate frames after success
```

Output: `assets/videos/fish.mp4` (~13.5 MB, 3 minutes, H.264 800×480).

### 3. Install RealVNC Server (so you can run headless)

You'll want to unplug the monitor and plug in the projector. Without VNC
you have no way to see the desktop. RealVNC is signed into a free account
(no static IP needed; cloud-discoverable from RealVNC Viewer).

```bash
wget https://downloads.realvnc.com/download/file/vnc.files/VNC-Server-7.16.0-Linux-x64.deb
sudo apt install -y ./VNC-Server-7.16.0-Linux-x64.deb
sudo systemctl enable --now vncserver-x11-serviced.service
vnclicensewiz   # GUI: sign into your RealVNC account
```

### 4. Force X11 (REQUIRED for VNC service-mode)

Ubuntu 24.04 defaults to Wayland. RealVNC Server in service mode can only
mirror an X11 session. Edit `/etc/gdm3/custom.conf`, uncomment:

```
WaylandEnable=false
```

Log out and back in (or reboot). Verify:

```bash
echo $XDG_SESSION_TYPE   # should print: x11
```

### 5. Connect the projector

- Plug HDMI from the mini-PC's spare HDMI port into the projector's HDMI input.
- Power on the projector — it boots into a source-selection menu.
- Select **HDMI** with the projector remote/buttons.
- The desktop should appear on the wall.

Verify with:
```bash
xrandr --query | grep -E "^HDMI"
```

### 6. Calibration

Generate a fullscreen test image with edge arrows and corner markers:

```bash
python3 calibration_image.py
DISPLAY=:1 XAUTHORITY=/run/user/$(id -u)/gdm/Xauthority \
    vlc --fullscreen --intf dummy --image-duration=-1 --loop \
    assets/videos/calibration.png
```

On the wall you should see TOP/BOTTOM/LEFT/RIGHT labels, four arrows
pointing to each edge, and a black square in each corner. If a corner
square is cut off, the projector is overshooting the wall.

Then measure the actual projected widths on the floor (top edge and
bottom edge) and use them to calibrate `PROJECTION_ANGLE_DEGREES` —
or just override the warp via `KEYSTONE_WIDTH_RATIO_OVERRIDE`.

### 7. Play the fish video fullscreen

```bash
DISPLAY=:1 XAUTHORITY=/run/user/$(id -u)/gdm/Xauthority \
    setsid vlc --fullscreen --loop --no-osd --no-video-title-show \
    --intf dummy assets/videos/fish.mp4 </dev/null &
```

(`setsid` + `</dev/null` ensures it survives the parent shell exiting.)

## Remote on/off — open issue

The RCA RPJ227 has **no network port, no HDMI-CEC, and no auto-power-on
after AC restore**. We verified this empirically: pulling and re-plugging
the AC adapter leaves the projector in standby (red LED). The lamp
requires a physical button press or an IR-remote command.

This means a smart plug *alone* is not enough — it can turn the projector
off but cannot turn it back on without a button press.

Solution being deployed: **Broadlink RM4 Mini** Wi-Fi IR blaster (~$20).
Workflow:

1. Use the Broadlink app once to learn the projector remote's "Power" code.
2. Install the Python `broadlink` library on this machine:
   ```bash
   pip install --user broadlink
   ```
3. Extend `telegram_bot.py`:
   - `/on`  → `broadlink.send(power_code)` → wait ~10 s for lamp warmup → start VLC
   - `/off` → kill VLC → `broadlink.send(power_code)` → projector to standby

In the meantime the Telegram bot can still control the *video* on/off
(the projector itself stays on). Lamp life on these projectors is rated
for 20–30k hours so this is fine for short cat-play sessions.

## Useful commands

```bash
# Verify session type (must be x11 for VNC mirror to work)
echo $XDG_SESSION_TYPE

# Find which DISPLAY the active X session is running on
ps -ef | grep Xorg | grep -v grep
loginctl list-sessions

# Start fish video on the projector
DISPLAY=:1 XAUTHORITY=/run/user/$(id -u)/gdm/Xauthority \
  setsid vlc --fullscreen --loop --no-osd --intf dummy \
  --no-video-title-show assets/videos/fish.mp4 </dev/null >/dev/null 2>&1 &

# Stop it
pkill -f 'vlc.*fish.mp4'

# Show the calibration grid
DISPLAY=:1 XAUTHORITY=/run/user/$(id -u)/gdm/Xauthority \
  setsid vlc --fullscreen --no-osd --intf dummy --image-duration=-1 --loop \
  --no-video-title-show assets/videos/calibration.png </dev/null >/dev/null 2>&1 &
```

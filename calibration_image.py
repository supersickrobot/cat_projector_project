"""Generate a fullscreen calibration image with arrows pointing to all four edges.

Useful for aligning the projector — verifies you can see the entire frame
without cropping at any edge, and helps spot keystone distortion.
"""
from PIL import Image, ImageDraw, ImageFont
import os

W, H = 1920, 1080
OUT = os.path.join(os.path.dirname(__file__), "assets", "videos", "calibration.png")
os.makedirs(os.path.dirname(OUT), exist_ok=True)

img = Image.new("RGB", (W, H), "white")
d = ImageDraw.Draw(img)

# Border frame (5px) so any pixel cropped at the edge is obvious
d.rectangle((0, 0, W - 1, H - 1), outline="black", width=5)

# Inner safe-area marker (5% inset, dashed-feel)
inset = int(W * 0.05)
d.rectangle((inset, inset, W - inset, H - inset), outline=(180, 180, 180), width=2)

cx, cy = W // 2, H // 2

# Crosshair at center
d.line((cx - 60, cy, cx + 60, cy), fill="black", width=4)
d.line((cx, cy - 60, cx, cy + 60), fill="black", width=4)
d.ellipse((cx - 18, cy - 18, cx + 18, cy + 18), outline="black", width=4)


def arrow(dx_from, dy_from, dx_to, dy_to, width=14, head=40, color="black"):
    """Draw an arrow from (dx_from, dy_from) to (dx_to, dy_to)."""
    d.line((dx_from, dy_from, dx_to, dy_to), fill=color, width=width)
    # Compute arrowhead direction
    import math
    ang = math.atan2(dy_to - dy_from, dx_to - dx_from)
    for sign in (-1, 1):
        a = ang + sign * math.radians(150)
        hx = dx_to + head * math.cos(a)
        hy = dy_to + head * math.sin(a)
        d.line((dx_to, dy_to, hx, hy), fill=color, width=width)


# Four arrows from center -> edges (stop just shy of the edge so arrowhead is visible)
margin = 30
arrow(cx, cy - 80, cx, margin, width=14, head=40)        # UP
arrow(cx, cy + 80, cx, H - margin, width=14, head=40)    # DOWN
arrow(cx - 80, cy, margin, cy, width=14, head=40)        # LEFT
arrow(cx + 80, cy, W - margin, cy, width=14, head=40)    # RIGHT

# Edge labels
try:
    font_big = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 64)
    font_med = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 36)
except OSError:
    font_big = ImageFont.load_default()
    font_med = ImageFont.load_default()

def text(xy, s, font=font_med, fill="black", anchor="mm"):
    d.text(xy, s, fill=fill, font=font, anchor=anchor)

text((cx, 90), "TOP", font=font_big)
text((cx, H - 90), "BOTTOM", font=font_big)
text((100, cy), "LEFT", font=font_big, anchor="lm")
text((W - 100, cy), "RIGHT", font=font_big, anchor="rm")

# Corner markers (filled black squares, 60×60) so you can confirm the corners reach the wall
m = 60
for (x, y) in [(0, 0), (W - m, 0), (0, H - m), (W - m, H - m)]:
    d.rectangle((x, y, x + m, y + m), fill="black")

# Resolution / aspect info center-bottom
text((cx, cy + 200), f"{W}x{H}  •  16:9", font=font_med)
text((cx, cy + 260), "Calibration: all 4 arrows + corner squares should be fully visible",
     font=ImageFont.load_default() if isinstance(font_med, type(ImageFont.load_default())) else
     ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24))

# Diagonal cross from corners to highlight keystone
d.line((0, 0, W, H), fill=(220, 220, 220), width=2)
d.line((W, 0, 0, H), fill=(220, 220, 220), width=2)

img.save(OUT)
print(f"Wrote calibration image: {OUT}  ({os.path.getsize(OUT)} bytes)")

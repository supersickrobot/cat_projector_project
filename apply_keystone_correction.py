"""Applies perspective (keystone) correction to animation frames so they project flat on the ground.
When a projector is mounted at an angle (e.g. 30 degrees from horizontal, pointing down from a shelf),
the projected image appears as a trapezoid on the floor. This script pre-warps each frame with the
INVERSE distortion so the final projected result looks rectangular and undistorted on the ground.

The math: a 30-degree downward tilt means the top of the image hits the floor closer to the shelf
(shorter throw) and the bottom hits further away (longer throw). The projected image is wider at
the bottom and narrower at the top. We counteract this by making the source image wider at the TOP
and narrower at the BOTTOM, so after projection the two distortions cancel out.
"""
import os
import math
import numpy as np
import cv2
from PIL import Image
import config


def compute_keystone_correction_matrix(width, height, angle_degrees):
    """Compute the perspective transform matrix that pre-warps frames to cancel projection distortion.
    Returns a 3x3 homography matrix. The angle is the projector tilt from horizontal (pointing down).
    """
    angle_radians = math.radians(angle_degrees)

    # The projector is tilted downward. The top of the projected image is closer to the projector
    # (shorter throw distance) so it appears narrower on the ground. The bottom is further away
    # so it appears wider. We need to apply the inverse: stretch the top, compress the bottom.

    # Scale factor = how much wider the bottom of the projected image is compared to the top.
    # For a flat surface, the ratio of widths is proportional to the throw distances.
    # At angle theta from horizontal:
    #   - Top edge throw distance is proportional to 1/cos(theta + delta)
    #   - Bottom edge throw distance is proportional to 1/cos(theta - delta)
    # where delta depends on the projector's vertical field of view.

    # For the RPJ227 with 800x480 and ~30 degree tilt, we use a simplified but effective approach:
    # We compute the trapezoid the image would project as, then map our rectangle into the
    # inverse trapezoid.

    # Vertical FOV approximation for the RPJ227 (roughly 30 degrees total vertical FOV)
    vertical_fov_degrees = 28.0
    half_vertical_fov = math.radians(vertical_fov_degrees / 2.0)

    # Top and bottom ray angles from horizontal
    top_ray_angle = angle_radians + half_vertical_fov
    bottom_ray_angle = angle_radians - half_vertical_fov

    # Relative width at top vs bottom (proportional to distance from projector to floor)
    # Distance to floor along ray = shelf_height / sin(ray_angle)
    # Width on floor proportional to distance
    top_distance = 1.0 / math.sin(top_ray_angle) if math.sin(top_ray_angle) > 0.01 else 100.0
    bottom_distance = 1.0 / math.sin(bottom_ray_angle) if math.sin(bottom_ray_angle) > 0.01 else 100.0

    # Ratio: how much wider the bottom is compared to the top in the projected image
    width_ratio = bottom_distance / top_distance

    # To cancel this, we need the INVERSE: make the top wider and bottom narrower in the source
    # The correction narrows the bottom by this ratio (or equivalently widens the top)
    # We'll express this as: top width = full width, bottom width = full width / width_ratio

    bottom_inset = width * (1.0 - 1.0 / width_ratio) / 2.0

    # Source corners (the rectangular frame we have)
    source_corners = np.float32([
        [0, 0],              # top-left
        [width, 0],          # top-right
        [width, height],     # bottom-right
        [0, height],         # bottom-left
    ])

    # Destination corners (the pre-warped trapezoid)
    # Top stays full width, bottom gets narrower (inset from both sides)
    destination_corners = np.float32([
        [0, 0],                              # top-left (unchanged)
        [width, 0],                          # top-right (unchanged)
        [width - bottom_inset, height],      # bottom-right (moved inward)
        [bottom_inset, height],              # bottom-left (moved inward)
    ])

    # Compute the perspective transform
    correction_matrix = cv2.getPerspectiveTransform(source_corners, destination_corners)

    print(f"Keystone correction for {angle_degrees}° tilt:")
    print(f"  Vertical FOV: {vertical_fov_degrees}°")
    print(f"  Width ratio (bottom/top in projection): {width_ratio:.3f}")
    print(f"  Bottom inset: {bottom_inset:.1f}px per side")
    print(f"  Effective bottom width: {width - 2 * bottom_inset:.0f}px (of {width}px)")

    return correction_matrix


def apply_correction_to_frame(frame_image, correction_matrix, width, height):
    """Apply the perspective warp to a single frame. Returns corrected PIL Image."""
    frame_array = np.array(frame_image)
    # Use white (255,255,255) as border fill since our background is white
    corrected_array = cv2.warpPerspective(
        frame_array, correction_matrix, (width, height),
        borderMode=cv2.BORDER_CONSTANT, borderValue=(255, 255, 255)
    )
    return Image.fromarray(corrected_array)


def correct_all_frames():
    """Apply keystone correction to all frames in the frames directory."""
    os.makedirs(config.CORRECTED_FRAMES_DIR, exist_ok=True)

    width = config.PROJECTOR_WIDTH
    height = config.PROJECTOR_HEIGHT

    correction_matrix = compute_keystone_correction_matrix(
        width, height, config.PROJECTION_ANGLE_DEGREES
    )

    # Get sorted list of frame files
    frame_files = sorted([
        f for f in os.listdir(config.FRAMES_DIR)
        if f.endswith(".png") and f.startswith("frame_")
    ])

    if not frame_files:
        print(f"No frames found in {config.FRAMES_DIR}. Run generate_fish_animation.py first.")
        return

    total_frames = len(frame_files)
    print(f"Applying keystone correction to {total_frames} frames...")
    print(f"  Input: {config.FRAMES_DIR}")
    print(f"  Output: {config.CORRECTED_FRAMES_DIR}")

    for index, filename in enumerate(frame_files):
        input_path = os.path.join(config.FRAMES_DIR, filename)
        output_path = os.path.join(config.CORRECTED_FRAMES_DIR, filename)

        frame_image = Image.open(input_path)
        corrected_image = apply_correction_to_frame(frame_image, correction_matrix, width, height)
        corrected_image.save(output_path)

        if index % 100 == 0:
            progress_percent = (index / total_frames) * 100
            print(f"  Frame {index}/{total_frames} ({progress_percent:.1f}%)")

    print(f"Done! {total_frames} corrected frames saved to {config.CORRECTED_FRAMES_DIR}")


def preview_correction():
    """Generate a single test image showing the correction grid for visual verification."""
    width = config.PROJECTOR_WIDTH
    height = config.PROJECTOR_HEIGHT

    # Create a grid test pattern
    test_image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(test_image)

    # Draw grid lines
    grid_spacing = 40
    for x in range(0, width, grid_spacing):
        draw.line([(x, 0), (x, height)], fill="gray", width=1)
    for y in range(0, height, grid_spacing):
        draw.line([(0, y), (width, y)], fill="gray", width=1)

    # Draw border
    draw.rectangle([(0, 0), (width - 1, height - 1)], outline="black", width=2)

    # Draw crosshair at center
    center_x, center_y = width // 2, height // 2
    draw.line([(center_x - 30, center_y), (center_x + 30, center_y)], fill="red", width=2)
    draw.line([(center_x, center_y - 30), (center_x, center_y + 30)], fill="red", width=2)

    # Apply correction
    correction_matrix = compute_keystone_correction_matrix(
        width, height, config.PROJECTION_ANGLE_DEGREES
    )
    corrected = apply_correction_to_frame(test_image, correction_matrix, width, height)

    # Save both
    os.makedirs(config.ASSETS_DIR, exist_ok=True)
    original_path = os.path.join(config.ASSETS_DIR, "test_grid_original.png")
    corrected_path = os.path.join(config.ASSETS_DIR, "test_grid_corrected.png")

    test_image.save(original_path)
    corrected.save(corrected_path)

    print(f"Preview saved:")
    print(f"  Original: {original_path}")
    print(f"  Corrected: {corrected_path}")
    print("Open both images to visually verify the correction looks right.")


# Need ImageDraw for preview function
from PIL import ImageDraw


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--preview":
        preview_correction()
    else:
        correct_all_frames()

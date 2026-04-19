"""Generates koi pond animation using biomechanically accurate fish swimming.
Fish body uses a traveling sine wave that propagates from head to tail (not simultaneous).
Amplitude increases from nearly zero at the head to maximum at the tail.
Body shape is wide and koi-proportioned with a blunt head and fan-shaped tail fin.
"""
import os
import math
import random
from PIL import Image, ImageDraw
import config

# Spine resolution — more points = smoother body
SPINE_POINTS = 12

# Koi body profile: (fraction along body, width as fraction of max_half_width)
# 0.0 = nose tip, 1.0 = tail peduncle
# Koi are widest at about 30% from the head, with a blunt rounded head
BODY_PROFILE = [
    (0.00, 0.10),   # nose tip
    (0.05, 0.50),   # snout — wide quickly (blunt head)
    (0.12, 0.80),   # forehead
    (0.25, 1.00),   # maximum width (just behind head)
    (0.40, 0.95),   # front body
    (0.55, 0.82),   # mid body
    (0.70, 0.60),   # rear body
    (0.82, 0.40),   # taper
    (0.92, 0.22),   # caudal peduncle (narrowest before tail)
    (1.00, 0.15),   # tail base
]


def interpolate_body_width(fraction_along_body):
    """Interpolate the body width profile at any position along the body (0=nose, 1=tail)."""
    if fraction_along_body <= 0:
        return BODY_PROFILE[0][1]
    if fraction_along_body >= 1:
        return BODY_PROFILE[-1][1]

    for i in range(len(BODY_PROFILE) - 1):
        position_a, width_a = BODY_PROFILE[i]
        position_b, width_b = BODY_PROFILE[i + 1]
        if position_a <= fraction_along_body <= position_b:
            local_fraction = (fraction_along_body - position_a) / (position_b - position_a)
            return width_a + (width_b - width_a) * local_fraction

    return BODY_PROFILE[-1][1]


class KoiFish:
    """A biomechanically accurate koi fish shadow."""

    def __init__(self, canvas_width, canvas_height):
        self.canvas_width = canvas_width
        self.canvas_height = canvas_height

        # Body dimensions — koi are wide, about 1:4 width-to-length ratio
        self.body_length = random.uniform(config.FISH_MIN_SIZE, config.FISH_MAX_SIZE)
        self.max_half_width = self.body_length * 0.12  # max half-width at widest point

        # Position and heading
        margin = self.body_length * 1.2
        self.x = random.uniform(margin, canvas_width - margin)
        self.y = random.uniform(margin, canvas_height - margin)
        self.heading = random.uniform(0, 2 * math.pi)

        # Waypoint-based steering (MIT Koi Pond style)
        # Fish pick random target points and smoothly steer toward them
        self.max_turn_rate = random.uniform(0.4, 0.8)    # radians/sec — wider sweeping curves
        self.waypoint_radius = self.body_length * 1.5     # when within this distance, pick new waypoint
        self.target_x, self.target_y = self.pick_new_waypoint()
        self.time_at_waypoint = 0.0
        self.waypoint_patience = random.uniform(3.0, 8.0)  # seconds before picking new waypoint even if not reached

        # Thrust-based speed (tail wags generate thrust, drag slows fish during coasting)
        # Calibrate thrust/drag so steady-state max speed ≈ FISH_MAX_SPEED
        self.drag_coefficient = random.uniform(2.0, 3.0)
        self.base_thrust = config.FISH_MAX_SPEED * self.drag_coefficient * 1.1  # slightly above max for responsiveness

        # Traveling wave parameters
        # The body wave propagates from head to tail
        self.wave_frequency = random.uniform(1.5, 2.5)     # Hz — how fast the wave cycles
        self.wave_phase = random.uniform(0, 2 * math.pi)
        self.max_tail_amplitude = self.body_length * 0.15   # max lateral displacement at tail tip (increased for visible body wave)
        self.wavelength_fraction = 1.0                       # one full wave along the body

        # Burst envelope — makes tail wag intermittent (active bursts + coasting periods)
        self.burst_frequency = random.uniform(0.15, 0.35)   # how often bursts happen
        self.burst_phase = random.uniform(0, 2 * math.pi)
        self.burst_duty_cycle = random.uniform(0.3, 0.5)    # fraction of time actively wagging

        # Tail fin parameters
        self.tail_fin_length = self.body_length * 0.15
        self.tail_fin_half_width = self.max_half_width * 0.8

        # Turn coupling — how strongly the tail wave asymmetry steers the fish
        self.turn_coupling_strength = random.uniform(0.3, 0.6)

        # Dynamic state
        self.current_speed = random.uniform(config.FISH_MIN_SPEED, config.FISH_MAX_SPEED)
        self.current_turn_rate = 0.0
        self.current_wave_amplitude = 1.0
        self.current_burst_amplitude = 0.0
        self.steering_curvature = 0.0  # body bend bias from steering (positive = curve left)

    def set_fish_list(self, fish_list):
        """Give this fish a reference to all fish for space-seeking behavior."""
        self.fish_list = fish_list

    def pick_new_waypoint(self):
        """Pick a waypoint biased toward empty space. Generates several candidates
        and picks the one farthest from the nearest other fish."""
        margin = self.body_length * 0.5  # reduced margin — fish can swim near edges
        candidates = []
        for _ in range(5):
            candidate = (
                random.uniform(margin, self.canvas_width - margin),
                random.uniform(margin, self.canvas_height - margin),
            )
            candidates.append(candidate)

        # If we have a fish list, score candidates by distance to nearest neighbor
        if hasattr(self, 'fish_list') and self.fish_list:
            best_candidate = candidates[0]
            best_min_distance = 0
            for candidate in candidates:
                min_distance = float('inf')
                for other in self.fish_list:
                    if other is self:
                        continue
                    distance = math.sqrt(
                        (candidate[0] - other.x) ** 2 + (candidate[1] - other.y) ** 2
                    )
                    min_distance = min(min_distance, distance)
                if min_distance > best_min_distance:
                    best_min_distance = min_distance
                    best_candidate = candidate
            return best_candidate

        return candidates[0]

    def compute_waypoint_steering(self):
        """Compute smooth turn rate toward the current waypoint.
        Returns a turn rate (radians/sec) clamped to max_turn_rate.
        """
        angle_to_target = math.atan2(self.target_y - self.y, self.target_x - self.x)
        angle_diff = angle_to_target - self.heading
        # Normalize to [-pi, pi]
        angle_diff = (angle_diff + math.pi) % (2 * math.pi) - math.pi
        # Smooth proportional steering, clamped to max turn rate
        desired_turn = angle_diff * 2.0  # proportional gain
        return max(-self.max_turn_rate, min(self.max_turn_rate, desired_turn))

    def compute_boundary_avoidance_turn(self):
        margin = self.body_length * 0.8  # reduced — fish can swim close to edges
        avoidance_strength = 2.0

        center_x = self.canvas_width / 2
        center_y = self.canvas_height / 2
        angle_to_center = math.atan2(center_y - self.y, center_x - self.x)

        proximity_factor = 0.0
        if self.x < margin:
            proximity_factor = max(proximity_factor, 1.0 - self.x / margin)
        elif self.x > self.canvas_width - margin:
            proximity_factor = max(proximity_factor, 1.0 - (self.canvas_width - self.x) / margin)
        if self.y < margin:
            proximity_factor = max(proximity_factor, 1.0 - self.y / margin)
        elif self.y > self.canvas_height - margin:
            proximity_factor = max(proximity_factor, 1.0 - (self.canvas_height - self.y) / margin)

        if proximity_factor > 0:
            angle_diff = angle_to_center - self.heading
            angle_diff = (angle_diff + math.pi) % (2 * math.pi) - math.pi
            return angle_diff * avoidance_strength * proximity_factor
        return 0.0

    def compute_burst_amplitude(self, time_seconds):
        """Compute the current burst envelope value (0 = coasting, 1 = full wag)."""
        burst_cycle = math.sin(2 * math.pi * self.burst_frequency * time_seconds + self.burst_phase)
        burst_threshold = 1.0 - 2.0 * self.burst_duty_cycle
        if burst_cycle > burst_threshold:
            return (burst_cycle - burst_threshold) / (1.0 - burst_threshold)
        return 0.08

    def compute_tail_lateral_force(self, time_seconds):
        """Compute the instantaneous lateral force from the tail wave.
        This is the cosine (derivative) of the tail's sine wave — positive means pushing left,
        which turns the fish right, and vice versa.
        """
        wave_time = 2 * math.pi * self.wave_frequency * time_seconds + self.wave_phase
        # Phase at the tail tip (fraction=1.0)
        tail_phase = wave_time - 2 * math.pi * self.wavelength_fraction
        # Lateral velocity is the derivative: cos(phase) * amplitude
        return math.cos(tail_phase) * self.current_burst_amplitude

    def update(self, time_seconds, delta_time):
        """Tu & Terzopoulos (1994) 'Artificial Fishes' locomotion model.
        The body curvature function c(s) IS the steering mechanism — heading change
        is derived from body curvature × speed, not applied independently.
        """
        # Compute burst envelope (intermittent swimming)
        self.current_burst_amplitude = self.compute_burst_amplitude(time_seconds)

        # Thrust from tail wag — proportional to burst amplitude
        thrust = self.base_thrust * self.current_burst_amplitude
        drag = self.drag_coefficient * self.current_speed
        speed_change = (thrust - drag) * delta_time
        self.current_speed += speed_change
        # Hard clamp speed to config range — no going below min or above max
        self.current_speed = max(config.FISH_MIN_SPEED, min(config.FISH_MAX_SPEED, self.current_speed))

        # Waypoint management
        distance_to_target = math.sqrt(
            (self.target_x - self.x) ** 2 + (self.target_y - self.y) ** 2
        )
        self.time_at_waypoint += delta_time
        if distance_to_target < self.waypoint_radius or self.time_at_waypoint > self.waypoint_patience:
            self.target_x, self.target_y = self.pick_new_waypoint()
            self.time_at_waypoint = 0.0
            self.waypoint_patience = random.uniform(3.0, 8.0)

        # Compute DESIRED curvature from waypoint steering + boundary avoidance
        # Tu & Terzopoulos: c_turn controls the body curvature function c(s) = c_turn * s
        desired_waypoint = self.compute_waypoint_steering()
        boundary_turn = self.compute_boundary_avoidance_turn()
        desired_turn = desired_waypoint + boundary_turn

        # The body curvature smoothly tracks the desired turn (muscle response lag)
        curvature_response_rate = 3.0  # how fast the body physically bends (rad/s)
        curvature_target = desired_turn * 0.8  # scale factor for visual curvature
        curvature_error = curvature_target - self.steering_curvature
        self.steering_curvature += curvature_error * min(1.0, curvature_response_rate * delta_time)

        # HEADING IS DERIVED FROM BODY CURVATURE × SPEED
        # Tu & Terzopoulos: angular velocity = c_turn × swimming_speed
        # The fish can only turn as fast as its body curves AND it has forward momentum
        curvature_heading_rate = self.steering_curvature * (self.current_speed / max(self.body_length * 0.5, 1.0))

        # Add subtle organic wobble from tail wave lateral force
        tail_force = self.compute_tail_lateral_force(time_seconds)
        wave_wobble = -tail_force * self.turn_coupling_strength * 0.15

        self.current_turn_rate = curvature_heading_rate + wave_wobble
        self.heading += self.current_turn_rate * delta_time
        self.heading = self.heading % (2 * math.pi)

        self.x += math.cos(self.heading) * self.current_speed * delta_time
        self.y += math.sin(self.heading) * self.current_speed * delta_time

        safety = self.body_length * 0.5
        self.x = max(safety, min(self.canvas_width - safety, self.x))
        self.y = max(safety, min(self.canvas_height - safety, self.y))

        # Wave visual amplitude scales with speed
        max_speed = self.base_thrust / self.drag_coefficient
        speed_ratio = self.current_speed / max(max_speed, 1.0)
        self.current_wave_amplitude = 0.3 + 0.7 * speed_ratio

    def compute_body_outline(self, time_seconds):
        """Compute the full body outline as two contour lists (left and right).
        Uses a traveling wave where each point along the spine is laterally displaced
        by a sine wave with increasing amplitude from head to tail, and phase that
        propagates backward (head leads, tail follows).
        """
        wave_time = 2 * math.pi * self.wave_frequency * time_seconds + self.wave_phase
        turn_bias = self.current_turn_rate * 0.08  # subtle head lean into turns

        # Burst envelope: smoothly ramps wave amplitude up and down
        # Creates intermittent swimming — active tail wag bursts with coasting in between
        burst_cycle = math.sin(2 * math.pi * self.burst_frequency * time_seconds + self.burst_phase)
        # Map sine (-1 to 1) through a threshold to create on/off periods
        # duty_cycle controls what fraction of time is "active"
        burst_threshold = 1.0 - 2.0 * self.burst_duty_cycle  # e.g. 0.3 duty → threshold 0.4
        if burst_cycle > burst_threshold:
            # Active period — smooth ramp from 0 to 1
            burst_amplitude = (burst_cycle - burst_threshold) / (1.0 - burst_threshold)
        else:
            # Coasting period — minimal residual motion
            burst_amplitude = 0.08

        # Generate spine centerline points
        spine_centerline = []
        left_contour = []
        right_contour = []

        segment_length = self.body_length / SPINE_POINTS

        # Build spine by chaining segments, each with a local angle that includes
        # the traveling wave lateral displacement
        current_x = self.x
        current_y = self.y

        # We build from the head position forward, then shift
        # Actually, let's compute head position first, then chain backward

        # Head is at the front. First compute spine angles for each point.
        spine_angles = []
        spine_positions = []

        for i in range(SPINE_POINTS + 1):
            fraction = i / SPINE_POINTS  # 0 = nose, 1 = tail

            # Traveling wave: phase increases from head to tail (wave propagates backward)
            # Amplitude increases quadratically from head to tail
            # Head has near-zero amplitude, tail has full amplitude
            amplitude_envelope = fraction * fraction  # quadratic increase toward tail
            wave_amplitude = self.max_tail_amplitude * amplitude_envelope * self.current_wave_amplitude * burst_amplitude

            # Phase offset: one full wavelength along the body
            phase_at_this_point = wave_time - fraction * 2 * math.pi * self.wavelength_fraction

            # Lateral displacement perpendicular to heading
            lateral_offset = wave_amplitude * math.sin(phase_at_this_point)

            # Add subtle turn bias to head region only
            head_bias = turn_bias * max(0, 1.0 - fraction * 4)  # fades out by 25% along body
            lateral_offset += head_bias

            # Steering curvature: bends the whole body toward the turn direction
            # Increases from zero at head to maximum at tail (body curves to steer)
            curvature_offset = -self.steering_curvature * self.body_length * 0.15 * fraction
            lateral_offset += curvature_offset

            # The local angle change due to the wave
            # This is the derivative of lateral_offset with respect to position
            wave_angle = math.atan2(lateral_offset, segment_length * 2)

            spine_angles.append(self.heading + wave_angle)

        # Now chain the spine positions from head backward
        # Start at temporary origin for head
        positions_relative = [(0.0, 0.0)]
        for i in range(1, SPINE_POINTS + 1):
            prev_x, prev_y = positions_relative[i - 1]
            angle = spine_angles[i - 1]
            positions_relative.append((
                prev_x - math.cos(angle) * segment_length,
                prev_y - math.sin(angle) * segment_length,
            ))

        # Shift so the point at fraction ~0.3 (widest) aligns with fish center
        anchor_index = int(SPINE_POINTS * 0.3)
        anchor_x, anchor_y = positions_relative[anchor_index]
        shift_x = self.x - anchor_x
        shift_y = self.y - anchor_y

        # Build final spine with positions and widths
        for i in range(SPINE_POINTS + 1):
            px, py = positions_relative[i]
            px += shift_x
            py += shift_y
            fraction = i / SPINE_POINTS

            half_width = self.max_half_width * interpolate_body_width(fraction)
            angle = spine_angles[i] if i < len(spine_angles) else spine_angles[-1]

            # Perpendicular offset for left and right contours
            perp_x = math.cos(angle + math.pi / 2) * half_width
            perp_y = math.sin(angle + math.pi / 2) * half_width

            spine_centerline.append((px, py))
            left_contour.append((px + perp_x, py + perp_y))
            right_contour.append((px - perp_x, py - perp_y))

        return spine_centerline, left_contour, right_contour

    def draw(self, draw_context, time_seconds):
        """Draw the fish as a single smooth filled body polygon plus tail fin."""
        spine, left_contour, right_contour = self.compute_body_outline(time_seconds)

        # Draw tail fin first (behind the body)
        self.draw_tail_fin(draw_context, spine, time_seconds)

        # Body is a single filled polygon: trace left contour forward, right contour backward
        body_polygon = left_contour + list(reversed(right_contour))
        if len(body_polygon) >= 3:
            draw_context.polygon(body_polygon, fill="black")

    def draw_tail_fin(self, draw_context, spine, time_seconds):
        """Draw a V-shaped tail fin at the tail end of the spine."""
        if len(spine) < 2:
            return

        tail_point = spine[-1]
        pre_tail_point = spine[-2]

        # Tail direction (points away from body)
        tail_direction_x = tail_point[0] - pre_tail_point[0]
        tail_direction_y = tail_point[1] - pre_tail_point[1]
        tail_angle = math.atan2(tail_direction_y, tail_direction_x)

        # Traveling wave at tail — the fin angle follows the wave
        wave_time = 2 * math.pi * self.wave_frequency * time_seconds + self.wave_phase
        fin_wave_offset = self.max_tail_amplitude * 1.5 * self.current_wave_amplitude * math.sin(
            wave_time - 2 * math.pi * self.wavelength_fraction
        )
        fin_angle = tail_angle + math.atan2(fin_wave_offset, self.tail_fin_length)

        cos_fin = math.cos(fin_angle)
        sin_fin = math.sin(fin_angle)
        cos_perp = math.cos(fin_angle + math.pi / 2)
        sin_perp = math.sin(fin_angle + math.pi / 2)

        base_x, base_y = tail_point
        fin_spread = self.tail_fin_half_width
        line_thickness = max(2, self.body_length * 0.015)  # thin lines that taper to points

        # V-shape: two line-like arms from the V-point (base) out to the tips
        # Upper arm tip — angled outward and backward
        upper_tip = (
            base_x + cos_fin * self.tail_fin_length + cos_perp * fin_spread,
            base_y + sin_fin * self.tail_fin_length + sin_perp * fin_spread,
        )
        # Lower arm tip — angled outward and backward
        lower_tip = (
            base_x + cos_fin * self.tail_fin_length - cos_perp * fin_spread,
            base_y + sin_fin * self.tail_fin_length - sin_perp * fin_spread,
        )

        # Each arm is a thin quad: wide at base (V-point), tapering to a point at tip
        # Upper arm
        base_width = line_thickness * 1.5
        upper_base_left = (base_x + cos_perp * base_width, base_y + sin_perp * base_width)
        upper_base_right = (base_x - cos_perp * base_width * 0.3, base_y - sin_perp * base_width * 0.3)
        draw_context.polygon([upper_base_left, upper_tip, upper_base_right], fill="black")

        # Lower arm
        lower_base_left = (base_x + cos_perp * base_width * 0.3, base_y + sin_perp * base_width * 0.3)
        lower_base_right = (base_x - cos_perp * base_width, base_y - sin_perp * base_width)
        draw_context.polygon([lower_base_left, lower_tip, lower_base_right], fill="black")


def generate_all_frames():
    """Render all animation frames to disk as PNG files."""
    os.makedirs(config.FRAMES_DIR, exist_ok=True)

    width = config.PROJECTOR_WIDTH
    height = config.PROJECTOR_HEIGHT
    total_frames = config.TOTAL_FRAMES
    fps = config.ANIMATION_FPS
    delta_time = 1.0 / fps

    fish_list = [KoiFish(width, height) for _ in range(config.FISH_COUNT)]
    for fish in fish_list:
        fish.set_fish_list(fish_list)

    print(f"Generating {total_frames} koi pond frames at {width}x{height} @ {fps}fps...")
    print(f"Fish count: {config.FISH_COUNT}, Spine points: {SPINE_POINTS}")
    print(f"Output: {config.FRAMES_DIR}")

    for frame_index in range(total_frames):
        time_seconds = frame_index / fps
        image = Image.new("RGB", (width, height), "white")
        draw_context = ImageDraw.Draw(image)

        for fish in fish_list:
            fish.update(time_seconds, delta_time)
            fish.draw(draw_context, time_seconds)

        frame_path = os.path.join(config.FRAMES_DIR, f"frame_{frame_index:06d}.png")
        image.save(frame_path)

        if frame_index % 100 == 0:
            progress_percent = (frame_index / total_frames) * 100
            print(f"  Frame {frame_index}/{total_frames} ({progress_percent:.1f}%)")

    print(f"Done! {total_frames} frames saved to {config.FRAMES_DIR}")


if __name__ == "__main__":
    generate_all_frames()

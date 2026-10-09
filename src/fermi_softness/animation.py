"""Camera turntables and bounded-memory MP4/GIF export."""

import copy
import json
import os
import subprocess
import tempfile
import time
from dataclasses import asdict
from itertools import product
from pathlib import Path

import numpy as np

from . import __version__
from .render import capture_camera, restore_camera

AXES = ("normal", "view", "x", "y", "z")


class ExportCancelled(RuntimeError):
    """The user cancelled; no partial output should be published."""


def rotation_axis(name, cell, camera):
    if name == "normal":
        cell = np.asarray(cell, dtype=float)
        axis = np.cross(cell[0], cell[1])
    elif name == "view":
        axis = np.asarray(camera["position"][2], dtype=float)
    elif name in ("x", "y", "z"):
        axis = np.eye(3)[("x", "y", "z").index(name)]
    else:
        raise ValueError("Rotation axis must be normal, view, x, y or z.")
    length = np.linalg.norm(axis)
    if axis.shape != (3,) or not np.isfinite(axis).all() or length < 1e-12:
        raise ValueError("The rotation axis must be a finite, nonzero vector.")
    return axis / length


def orbit_camera(camera, axis, degrees):
    """Rotate position and view-up about the focal point without changing zoom."""
    axis = np.asarray(axis, dtype=float)
    position = np.asarray(camera["position"], dtype=float)
    if (
        axis.shape != (3,) or position.shape != (3, 3)
        or not np.isfinite(position).all() or not np.isfinite(axis).all()
        or not np.isfinite(degrees) or np.linalg.norm(axis) < 1e-12
    ):
        raise ValueError("Invalid camera or rotation axis.")
    axis = axis / np.linalg.norm(axis)
    angle = np.deg2rad(degrees)

    def rotate(vector):
        return (vector * np.cos(angle) + np.cross(axis, vector) * np.sin(angle)
                + axis * np.dot(axis, vector) * (1 - np.cos(angle)))

    eye, focus, up = position
    result = copy.deepcopy(camera)
    result["position"] = [
        (focus + rotate(eye - focus)).tolist(), focus.tolist(), rotate(up).tolist()
    ]
    return result


def fit_rotation_camera(camera, bounds, width, height, orthographic):
    """Fit a sphere about the current focal point, safe for every rotation angle."""
    bounds = np.asarray(bounds, dtype=float).reshape(3, 2)
    if not np.isfinite(bounds).all() or np.any(bounds[:, 0] > bounds[:, 1]):
        raise ValueError("Cannot frame invalid scene bounds.")
    result = copy.deepcopy(camera)
    eye, focus, _ = np.asarray(camera["position"], dtype=float)
    corners = np.array(list(product(*bounds)))
    radius = float(np.linalg.norm(corners - focus, axis=1).max()) * 1.12
    aspect = width / height
    if orthographic:
        result["parallel_scale"] = max(camera["parallel_scale"], radius / min(1., aspect))
    else:
        angle = np.deg2rad(camera.get("view_angle", 30) / 2)
        half_angle = min(angle, np.arctan(np.tan(angle) * aspect))
        direction = eye - focus
        distance = np.linalg.norm(direction)
        if distance < 1e-12 or not 0 < half_angle < np.pi / 2:
            raise ValueError("Invalid perspective camera for animation.")
        distance_needed = radius / np.sin(half_angle)
        result["position"][0] = (focus + direction * max(1., distance_needed / distance)).tolist()
    return result


def validate_animation(path, width, height, fps, seconds, turns):
    path = Path(path)
    if path.suffix.lower() not in (".mp4", ".gif"):
        raise ValueError("Choose an MP4 or GIF output file.")
    if any(int(x) != x or not 128 <= x <= 4096 for x in (width, height)):
        raise ValueError("Animation width and height must be 128–4096 pixels.")
    if width % 2 or height % 2:
        raise ValueError("Animation width and height must be even numbers.")
    if int(fps) != fps or not 1 <= fps <= 60:
        raise ValueError("Frame rate must be an integer from 1 to 60 fps.")
    if not np.isfinite(seconds) or not 0.25 <= seconds <= 120:
        raise ValueError("Animation duration must be 0.25–120 seconds.")
    if int(turns) != turns or not 1 <= turns <= 10:
        raise ValueError("Choose between 1 and 10 full rotations.")
    frames = int(round(seconds * fps))
    if frames < 2:
        raise ValueError("An animation needs at least two frames.")
    return frames


class MovieWriter:
    """Stream frames to FFmpeg, then publish complete outputs exclusively."""

    def __init__(self, path, width, height, fps, *, cancelled=None, pulse=None):
        import imageio_ffmpeg

        self.path = Path(path)
        self.width, self.height, self.fps = width, height, fps
        self.targets = [self.path, Path(str(path) + ".scene.json"),
                        Path(str(path) + ".animation.json")]
        if any(p.exists() or p.is_symlink() for p in self.targets):
            raise ValueError("Animation output already exists. Choose a new filename.")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
        self.cancelled = cancelled or (lambda: False)
        self.pulse = pulse or (lambda: None)
        self.temporary = tempfile.TemporaryDirectory(
            prefix=".fermi-animation-", dir=self.path.parent
        )
        self.root = Path(self.temporary.name)
        self.video = self.root / "movie.mp4"
        self.log = (self.root / "ffmpeg.log").open("wb")
        self.process = None
        try:
            command = [
                self.ffmpeg, "-hide_banner", "-loglevel", "error", "-nostdin", "-y",
                "-f", "rawvideo", "-vcodec", "rawvideo", "-pix_fmt", "rgb24",
                "-s", f"{width}x{height}", "-r", str(fps), "-i", "-", "-an",
                "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(self.video),
            ]
            self.process = subprocess.Popen(
                command, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=self.log
            )
        except BaseException:
            self.close()
            raise

    def check_cancelled(self):
        self.pulse()
        if self.cancelled():
            raise ExportCancelled("Animation export cancelled.")

    def encoder_error(self):
        self.log.flush()
        detail = (self.root / "ffmpeg.log").read_text(errors="replace")[-2000:]
        return RuntimeError("Animation encoder failed. " + detail.strip())

    def append(self, pixels):
        self.check_cancelled()
        pixels = np.asarray(pixels)
        if pixels.dtype != np.uint8 or pixels.shape != (self.height, self.width, 3):
            raise ValueError("The rendered frame has an unexpected size or RGB format.")
        try:
            self.process.stdin.write(np.ascontiguousarray(pixels).tobytes())
        except (BrokenPipeError, OSError) as exc:
            raise self.encoder_error() from exc

    def wait_encoder(self):
        while self.process.poll() is None:
            self.check_cancelled()
            time.sleep(0.03)
        if self.process.returncode:
            raise self.encoder_error()

    def run_filter(self, arguments):
        self.check_cancelled()
        self.process = subprocess.Popen(
            [self.ffmpeg, "-hide_banner", "-loglevel", "error", "-nostdin", "-y"]
            + arguments, stdout=subprocess.DEVNULL, stderr=self.log
        )
        self.wait_encoder()

    def finish(self, scene, metadata, *, stage=None):
        try:
            self.process.stdin.close()
        except BrokenPipeError as exc:
            raise self.encoder_error() from exc
        self.wait_encoder()
        movie = self.video
        if self.path.suffix.lower() == ".gif":
            if stage:
                stage("Optimizing GIF palette")
            palette = self.root / "palette.png"
            # Two passes avoid retaining a whole animation while its palette is built.
            self.run_filter(["-i", str(self.video), "-vf", "palettegen=stats_mode=full",
                             "-frames:v", "1", "-threads", "1", str(palette)])
            if stage:
                stage("Encoding GIF")
            movie = self.root / "movie.gif"
            self.run_filter(["-i", str(self.video), "-i", str(palette),
                             "-lavfi", "paletteuse=dither=sierra2_4a", "-loop", "0",
                             str(movie)])
        if not movie.is_file() or movie.stat().st_size == 0:
            raise RuntimeError("The encoder did not produce an animation.")
        scene_file, info_file = self.root / "scene.json", self.root / "animation.json"
        scene_file.write_text(json.dumps(asdict(scene), indent=2, allow_nan=False) + "\n")
        info_file.write_text(json.dumps(metadata, indent=2, allow_nan=False) + "\n")
        self.check_cancelled()
        created = []
        try:
            # Link only completed files. Never overwrite another result, including races.
            for source, target in zip((movie, scene_file, info_file), self.targets):
                os.link(source, target)
                created.append(target)
        except BaseException:
            for target in created:
                target.unlink()
            raise

    def close(self):
        if self.process is not None and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
        if self.process is not None and self.process.stdin is not None:
            try:
                self.process.stdin.close()
            except BrokenPipeError:
                pass
        self.log.close()
        self.temporary.cleanup()


def export_animation(
    plotter, path, scene, cell, *, width=1920, height=1080, fps=30, seconds=12,
    turns=1, axis="normal", reverse=False, fit=True, progress=None, cancelled=None, pulse=None,
):
    """Export the current scene, keeping colors fixed and restoring the live view."""
    frames = validate_animation(path, width, height, fps, seconds, turns)
    original = capture_camera(plotter)
    start = (fit_rotation_camera(original, plotter.bounds, width, height, scene.orthographic)
             if fit else original)
    vector = rotation_axis(axis, cell, start)
    old_size = tuple(plotter.window_size)
    saved_scene = copy.deepcopy(scene)
    saved_scene.camera = start
    direction = -1 if reverse else 1
    metadata = {
        "schema": "fermi-softness-animation-1", "software": "fermi-softness",
        "version": __version__, "frames": frames, "fps": fps,
        "width": width, "height": height, "duration_seconds": frames / fps,
        "requested_duration_seconds": seconds, "turns": turns, "axis": axis,
        "axis_vector": vector.tolist(), "reverse": bool(reverse),
        "fit_rotation": bool(fit),
        "duplicate_endpoint": False, "color_range_fixed": True,
        "color_range_eV_inverse_Angstrom_inverse3": [scene.color_min, scene.color_max],
        "scene_file": Path(str(path) + ".scene.json").name,
        "format": Path(path).suffix.lower()[1:],
    }
    writer = MovieWriter(path, width, height, fps, cancelled=cancelled, pulse=pulse)
    try:
        for index in range(frames):
            writer.check_cancelled()
            camera = orbit_camera(start, vector, direction * 360 * turns * index / frames)
            restore_camera(plotter, camera)
            plotter.reset_camera_clipping_range()
            plotter.render()
            pixels = plotter.screenshot(
                return_img=True, window_size=(width, height), transparent_background=False
            )
            writer.append(pixels[:, :, :3])
            if progress:
                progress(index + 1, frames, "Rendering animation")
        if progress:
            progress(frames, frames, "Finishing video")
        writer.finish(saved_scene, metadata, stage=(
            (lambda label: progress(frames, frames, label)) if progress else None
        ))
        return metadata
    finally:
        try:
            writer.close()
        finally:
            restore_camera(plotter, original)
            plotter.window_size = old_size
            plotter.reset_camera_clipping_range()
            plotter.render()


def render_animation(field, path, scene, charge=None, **options):
    """Render full frames at the output resolution, separate from any Qt widget."""
    import pyvista as pv

    from .render import draw_scene

    width, height = options.get("width", 1920), options.get("height", 1080)
    validate_animation(path, width, height, options.get("fps", 30),
                       options.get("seconds", 12), options.get("turns", 1))
    plotter = pv.Plotter(off_screen=True, window_size=(width, height))
    try:
        draw_scene(plotter, field, scene, charge)
        return export_animation(plotter, path, scene, field.cell, **options)
    finally:
        plotter.close()

#!/usr/bin/env python3
"""
Digital Harmony Group Graphics Resizer V1.5
=============================================
Double-click to launch. No terminal required.

A user-friendly desktop app for batch resizing headshots to uniform dimensions
with optional AI background removal and replacement.

Works on macOS and Windows with Python 3.9+.
Requires: Pillow (auto-installs on first run)
Optional: rembg (auto-installs if background removal is selected)

Built by Digital Harmony Group
"""

import json
import math
import os
import subprocess
import sys
import threading
from pathlib import Path

# ---------------------------------------------------------------------------
# Dependency check — the platform launcher (.command / .bat) installs these
# into a .venv before running this script. If someone runs the .py directly,
# give them a clear error pointing to the launcher.
# ---------------------------------------------------------------------------

_LAUNCH_HINT = (
    "\n  Use the platform launcher instead:\n"
    "    Mac:     Double-click 'Launch Headshot Resizer.command'\n"
    "    Windows: Double-click 'Launch Headshot Resizer.bat'\n"
    "\n  The launcher creates a virtual environment and installs everything automatically."
)

try:
    from PIL import Image, ImageDraw, ImageOps
except ImportError:
    print("Pillow is not installed." + _LAUNCH_HINT)
    sys.exit(1)

try:
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox
except ImportError:
    print("tkinter is not available." + _LAUNCH_HINT)
    if sys.platform == "darwin":
        pyver = f"{sys.version_info.major}.{sys.version_info.minor}"
        print(f"\n  On macOS with Homebrew, also run:  brew install python-tk@{pyver}")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Image processing engine (self-contained — no external script dependency)
# ---------------------------------------------------------------------------

SUPPORTED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.tiff', '.tif', '.bmp', '.gif'}


def hex_to_rgb(hex_str: str) -> tuple:
    h = hex_str.lstrip('#')
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def is_hex_color(s: str) -> bool:
    s = s.lstrip('#')
    if len(s) not in (3, 6):
        return False
    try:
        int(s, 16)
        return True
    except ValueError:
        return False


def lerp_color(c1, c2, t):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


def multi_stop_color(colors, t):
    if len(colors) == 1:
        return colors[0]
    n = len(colors) - 1
    segment = min(int(t * n), n - 1)
    local_t = (t * n) - segment
    return lerp_color(colors[segment], colors[segment + 1], local_t)


GRADIENT_DIRECTIONS = {'down', 'right', 'diagonal', 'radial'}


def parse_bg_spec(bg_str: str) -> dict:
    if bg_str.upper() == 'TRANSPARENT':
        return {'type': 'transparent'}
    if os.path.isfile(bg_str):
        return {'type': 'image', 'path': bg_str}
    parts = bg_str.split(':')
    hex_parts = [p for p in parts if is_hex_color(p)]
    dir_parts = [p.lower() for p in parts if p.lower() in GRADIENT_DIRECTIONS]
    if len(hex_parts) >= 2:
        colors = [hex_to_rgb(h) for h in hex_parts]
        direction = dir_parts[0] if dir_parts else 'down'
        return {'type': 'gradient', 'colors': colors, 'direction': direction}
    if len(hex_parts) == 1:
        return {'type': 'solid', 'color': hex_parts[0]}
    if is_hex_color(bg_str):
        return {'type': 'solid', 'color': bg_str}
    return {'type': 'solid', 'color': '#FFFFFF'}


def create_gradient(width, height, colors, direction='down'):
    img = Image.new('RGB', (width, height))
    draw = ImageDraw.Draw(img)
    if direction == 'down':
        for y in range(height):
            t = y / max(height - 1, 1)
            c = multi_stop_color(colors, t)
            draw.line([(0, y), (width, y)], fill=c)
    elif direction == 'right':
        for x in range(width):
            t = x / max(width - 1, 1)
            c = multi_stop_color(colors, t)
            draw.line([(x, 0), (x, height)], fill=c)
    elif direction == 'diagonal':
        max_dist = math.sqrt(width ** 2 + height ** 2)
        for y in range(height):
            for x in range(width):
                dist = math.sqrt(x ** 2 + y ** 2)
                t = dist / max_dist
                img.putpixel((x, y), multi_stop_color(colors, t))
    elif direction == 'radial':
        cx, cy = width / 2, height / 2
        max_r = math.sqrt(cx ** 2 + cy ** 2)
        for y in range(height):
            for x in range(width):
                r = math.sqrt((x - cx) ** 2 + (y - cy) ** 2)
                t = min(r / max_r, 1.0)
                img.putpixel((x, y), multi_stop_color(colors, t))
    return img


def create_background(bg_spec, width, height):
    if bg_spec['type'] == 'solid':
        color = hex_to_rgb(bg_spec['color'])
        return Image.new('RGB', (width, height), color)
    elif bg_spec['type'] == 'gradient':
        return create_gradient(width, height, bg_spec['colors'], bg_spec['direction'])
    elif bg_spec['type'] == 'image':
        bg = Image.open(bg_spec['path']).convert('RGB')
        return ImageOps.fit(bg, (width, height), method=Image.LANCZOS)
    elif bg_spec['type'] == 'transparent':
        return Image.new('RGBA', (width, height), (0, 0, 0, 0))
    return Image.new('RGB', (width, height), (255, 255, 255))


def fix_orientation(img):
    try:
        return ImageOps.exif_transpose(img)
    except Exception:
        return img


def crop_center(img, target_w, target_h):
    ratio = max(target_w / img.width, target_h / img.height)
    new_w = int(img.width * ratio)
    new_h = int(img.height * ratio)
    img = img.resize((new_w, new_h), Image.LANCZOS)
    left = (new_w - target_w) // 2
    top = (new_h - target_h) // 2
    return img.crop((left, top, left + target_w, top + target_h))


def crop_top(img, target_w, target_h):
    ratio = max(target_w / img.width, target_h / img.height)
    new_w = int(img.width * ratio)
    new_h = int(img.height * ratio)
    img = img.resize((new_w, new_h), Image.LANCZOS)
    left = (new_w - target_w) // 2
    return img.crop((left, 0, left + target_w, target_h))


def fill_resize(img, target_w, target_h, bg_spec=None):
    ratio = min(target_w / img.width, target_h / img.height)
    new_w = int(img.width * ratio)
    new_h = int(img.height * ratio)
    resized = img.resize((new_w, new_h), Image.LANCZOS)
    if bg_spec and bg_spec['type'] != 'transparent':
        canvas = create_background(bg_spec, target_w, target_h)
    else:
        canvas = Image.new('RGBA', (target_w, target_h), (0, 0, 0, 0))
    offset_x = (target_w - new_w) // 2
    offset_y = (target_h - new_h) // 2
    if resized.mode == 'RGBA':
        canvas.paste(resized, (offset_x, offset_y), resized)
    else:
        canvas.paste(resized, (offset_x, offset_y))
    return canvas


def composite_on_background(fg, bg_spec, width, height, crop_mode="top"):
    """Composite foreground onto background, scaling to FILL the canvas.

    Uses max() ratio so the subject fills the entire target area.
    crop_mode controls vertical alignment:
      'top'    -- align subject to top (preserves heads in portraits)
      'center' -- center subject vertically
      'fill'   -- shrink-to-fit with padding (no cropping)
    """
    if crop_mode == "fill":
        ratio = min(width / fg.width, height / fg.height)
    else:
        ratio = max(width / fg.width, height / fg.height)

    new_w = int(fg.width * ratio)
    new_h = int(fg.height * ratio)
    fg_resized = fg.resize((new_w, new_h), Image.LANCZOS)

    if bg_spec['type'] == 'transparent':
        canvas = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    else:
        canvas = create_background(bg_spec, width, height)
        if canvas.mode != 'RGBA':
            canvas = canvas.convert('RGBA')

    offset_x = (width - new_w) // 2

    if crop_mode == "top":
        offset_y = 0
    else:
        offset_y = (height - new_h) // 2

    canvas.paste(fg_resized, (offset_x, offset_y), fg_resized)
    return canvas


_rembg_sessions = {}

# ---------------------------------------------------------------------------
# Background Removal Workflows
# ---------------------------------------------------------------------------

BG_WORKFLOWS = {
    "portrait": {
        "label": "Portrait (BiRefNet-Portrait)",
        "description": "Best for headshots and people. Exceptional hair and shoulder edge quality.",
        "model": "birefnet-portrait",
        "blur_radius": 0.8,
        "threshold_low": 15,
        "alpha_boost": 1.08,
    },
    "general": {
        "label": "General Purpose (BiRefNet-General)",
        "description": "Best all-around model. Great for products, objects, and mixed content.",
        "model": "birefnet-general",
        "blur_radius": 1.0,
        "threshold_low": 20,
        "alpha_boost": 1.05,
    },
    "bria": {
        "label": "High Detail (BRIA RMBG)",
        "description": "State-of-the-art by BRIA AI. Excels at complex scenes and fine textures.",
        "model": "bria-rmbg",
        "blur_radius": 0.6,
        "threshold_low": 12,
        "alpha_boost": 1.10,
    },
}


def _get_session(model_name):
    """Lazily load and cache a rembg model session."""
    global _rembg_sessions
    if model_name not in _rembg_sessions:
        from rembg import new_session
        _rembg_sessions[model_name] = new_session(model_name)
    return _rembg_sessions[model_name]


def _refine_alpha(img, blur_radius=1.0, threshold_low=20, alpha_boost=1.05):
    """Refine the alpha mask for cleaner edges."""
    from PIL import ImageFilter

    if img.mode != "RGBA":
        return img

    r, g, b, a = img.split()
    a_smooth = a.filter(ImageFilter.GaussianBlur(radius=blur_radius))
    a_clean = a_smooth.point(
        lambda x: 0 if x < threshold_low else min(255, int(x * alpha_boost))
    )
    return Image.merge("RGBA", (r, g, b, a_clean))


def remove_background(img, workflow_key="portrait"):
    """Remove background using the specified workflow."""
    from rembg import remove

    wf = BG_WORKFLOWS[workflow_key]
    session = _get_session(wf["model"])

    result = remove(
        img,
        session=session,
        post_process_mask=True,
    )
    return _refine_alpha(
        result,
        blur_radius=wf["blur_radius"],
        threshold_low=wf["threshold_low"],
        alpha_boost=wf["alpha_boost"],
    )


# ---------------------------------------------------------------------------
# GUI Application
# ---------------------------------------------------------------------------

class HeadshotResizerApp:
    """Tkinter GUI for batch headshot resizing."""

    BG_PRESETS = {
        "White (#FFFFFF)": "#FFFFFF",
        "Light Gray (#E0E0E0)": "#E0E0E0",
        "Professional Gray (#D0D0D0)": "#D0D0D0",
        "Corporate Blue Gradient": "#4A7AB5:#E8EEF5",
        "NACE Brand Gradient": "#1D4BB7:#DFE7EF",
        "NACE Full Gradient": "#1D4BB7:#DFE7EF:#1D4BB7",
        "ONA Teal (#49A3A1)": "#49A3A1",
        "ONA Summit Gradient": "#49A3A1:#FFFFFF",
        "Transparent (PNG only)": "TRANSPARENT",
        "Custom...": "CUSTOM",
    }

    SIZE_PRESETS = {
        "500 x 500 -- Headshot (Web)": (500, 500),
        "400 x 400 -- Headshot (Thumbnail)": (400, 400),
        "300 x 300 -- Headshot (Small)": (300, 300),
        "200 x 200 -- Avatar / Icon": (200, 200),
        "800 x 800 -- Headshot (High-res)": (800, 800),
        "170 x 170 -- Facebook Profile": (170, 170),
        "320 x 320 -- Instagram Profile": (320, 320),
        "400 x 400 -- X / Twitter Profile": (400, 400),
        "400 x 400 -- LinkedIn Profile": (400, 400),
        "800 x 800 -- YouTube Profile": (800, 800),
        "1080 x 1080 -- Instagram Post (Square)": (1080, 1080),
        "1080 x 1350 -- Instagram Post (Portrait)": (1080, 1350),
        "1080 x 566 -- Instagram Post (Landscape)": (1080, 566),
        "1080 x 1920 -- Instagram / TikTok Story": (1080, 1920),
        "1200 x 630 -- Facebook Post / Link": (1200, 630),
        "1200 x 675 -- X / Twitter Post": (1200, 675),
        "1200 x 627 -- LinkedIn Post": (1200, 627),
        "1000 x 1500 -- Pinterest Pin": (1000, 1500),
        "1280 x 720 -- YouTube Thumbnail": (1280, 720),
        "820 x 312 -- Facebook Cover": (820, 312),
        "1500 x 500 -- X / Twitter Header": (1500, 500),
        "1584 x 396 -- LinkedIn Banner": (1584, 396),
        "2560 x 1440 -- YouTube Channel Banner": (2560, 1440),
        "300 x 250 -- Medium Rectangle (IAB)": (300, 250),
        "728 x 90 -- Leaderboard (IAB)": (728, 90),
        "160 x 600 -- Wide Skyscraper (IAB)": (160, 600),
        "300 x 600 -- Half Page (IAB)": (300, 600),
        "320 x 50 -- Mobile Leaderboard (IAB)": (320, 50),
        "320 x 480 -- Mobile Interstitial (IAB)": (320, 480),
        "970 x 250 -- Billboard (IAB)": (970, 250),
        "970 x 90 -- Large Leaderboard (IAB)": (970, 90),
        "600 x 200 -- Email Header": (600, 200),
        "600 x 600 -- Email Square": (600, 600),
        "1200 x 400 -- Website Hero Banner": (1200, 400),
        "1920 x 1080 -- Full HD (16:9)": (1920, 1080),
        "Custom...": (0, 0),
    }

    def __init__(self, root):
        self.root = root
        self.root.title("Digital Harmony Group Graphics Resizer V1.5")
        self.root.resizable(True, True)
        self.root.minsize(680, 780)

        self.input_dir = tk.StringVar()
        self.output_dir = tk.StringVar()
        self.size_preset = tk.StringVar(value="500 x 500 -- Headshot (Web)")
        self.custom_width = tk.StringVar(value="500")
        self.custom_height = tk.StringVar(value="500")
        self.crop_mode = tk.StringVar(value="top")
        self.output_format = tk.StringVar(value="JPEG")
        self.quality = tk.IntVar(value=95)
        self.remove_bg = tk.BooleanVar(value=False)
        self.wf_portrait = tk.BooleanVar(value=False)
        self.wf_general = tk.BooleanVar(value=False)
        self.wf_bria = tk.BooleanVar(value=False)
        self.bg_preset = tk.StringVar(value="White (#FFFFFF)")
        self.custom_bg = tk.StringVar(value="#E0E0E0")
        self.is_processing = False

        self._build_ui()
        self._center_window()

    def _center_window(self):
        self.root.update_idletasks()
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (w // 2)
        y = (self.root.winfo_screenheight() // 2) - (h // 2)
        self.root.geometry(f"+{x}+{y}")

    def _build_ui(self):
        style = ttk.Style()
        try:
            style.theme_use("aqua")
        except Exception:
            try:
                style.theme_use("vista")
            except Exception:
                style.theme_use("clam")

        main = ttk.Frame(self.root, padding=20)
        main.grid(row=0, column=0, sticky="nsew")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main.columnconfigure(1, weight=1)

        row = 0

        title = ttk.Label(main, text="Digital Harmony Group Graphics Resizer", font=("Helvetica", 18, "bold"))
        title.grid(row=row, column=0, columnspan=3, pady=(0, 5), sticky="w")
        row += 1

        subtitle = ttk.Label(main, text="Version 1.5 -- Resize, crop, and replace backgrounds on batches of photos.",
                             font=("Helvetica", 11))
        subtitle.grid(row=row, column=0, columnspan=3, pady=(0, 15), sticky="w")
        row += 1

        ttk.Label(main, text="Input Folder:", font=("Helvetica", 11, "bold")).grid(
            row=row, column=0, sticky="w", pady=(5, 2))
        row += 1

        input_frame = ttk.Frame(main)
        input_frame.grid(row=row, column=0, columnspan=3, sticky="ew", pady=(0, 8))
        input_frame.columnconfigure(0, weight=1)
        ttk.Entry(input_frame, textvariable=self.input_dir).grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ttk.Button(input_frame, text="Browse...", command=self._browse_input).grid(row=0, column=1)
        row += 1

        ttk.Label(main, text="Output Folder:", font=("Helvetica", 11, "bold")).grid(
            row=row, column=0, sticky="w", pady=(5, 2))
        row += 1

        output_frame = ttk.Frame(main)
        output_frame.grid(row=row, column=0, columnspan=3, sticky="ew", pady=(0, 12))
        output_frame.columnconfigure(0, weight=1)
        ttk.Entry(output_frame, textvariable=self.output_dir).grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ttk.Button(output_frame, text="Browse...", command=self._browse_output).grid(row=0, column=1)
        row += 1

        ttk.Separator(main, orient="horizontal").grid(row=row, column=0, columnspan=3, sticky="ew", pady=8)
        row += 1

        ttk.Label(main, text="Output Size:", font=("Helvetica", 11, "bold")).grid(
            row=row, column=0, sticky="w", pady=(5, 2))
        row += 1

        size_combo = ttk.Combobox(main, textvariable=self.size_preset,
                                   values=list(self.SIZE_PRESETS.keys()), state="readonly", width=48)
        size_combo.grid(row=row, column=0, columnspan=2, sticky="w", pady=(0, 4))
        size_combo.bind("<<ComboboxSelected>>", self._on_size_change)
        row += 1

        self.custom_size_frame = ttk.Frame(main)
        self.custom_size_frame.grid(row=row, column=0, columnspan=3, sticky="w", pady=(0, 8))
        ttk.Label(self.custom_size_frame, text="Width:").grid(row=0, column=0, padx=(0, 4))
        ttk.Entry(self.custom_size_frame, textvariable=self.custom_width, width=6).grid(row=0, column=1, padx=(0, 12))
        ttk.Label(self.custom_size_frame, text="Height:").grid(row=0, column=2, padx=(0, 4))
        ttk.Entry(self.custom_size_frame, textvariable=self.custom_height, width=6).grid(row=0, column=3)
        self.custom_size_frame.grid_remove()
        row += 1

        ttk.Label(main, text="Crop Mode:", font=("Helvetica", 11, "bold")).grid(
            row=row, column=0, sticky="w", pady=(5, 2))
        row += 1

        crop_frame = ttk.Frame(main)
        crop_frame.grid(row=row, column=0, columnspan=3, sticky="w", pady=(0, 8))
        for i, (label, value) in enumerate([
            ("Top (best for headshots)", "top"),
            ("Center crop", "center"),
            ("Fill (no crop, pad edges)", "fill"),
        ]):
            ttk.Radiobutton(crop_frame, text=label, variable=self.crop_mode, value=value).grid(
                row=0, column=i, padx=(0, 16))
        row += 1

        fmt_frame = ttk.Frame(main)
        fmt_frame.grid(row=row, column=0, columnspan=3, sticky="w", pady=(0, 8))
        ttk.Label(fmt_frame, text="Format:", font=("Helvetica", 11, "bold")).grid(row=0, column=0, padx=(0, 8))
        for i, fmt in enumerate(["JPEG", "PNG", "WEBP"]):
            ttk.Radiobutton(fmt_frame, text=fmt, variable=self.output_format, value=fmt).grid(
                row=0, column=i + 1, padx=(0, 12))
        ttk.Label(fmt_frame, text="Quality:").grid(row=0, column=4, padx=(16, 4))
        ttk.Spinbox(fmt_frame, from_=50, to=100, textvariable=self.quality, width=4).grid(row=0, column=5)
        row += 1

        ttk.Separator(main, orient="horizontal").grid(row=row, column=0, columnspan=3, sticky="ew", pady=8)
        row += 1

        bg_check = ttk.Checkbutton(main, text="Remove & Replace Backgrounds (AI)",
                                    variable=self.remove_bg, command=self._toggle_bg_options)
        bg_check.grid(row=row, column=0, columnspan=3, sticky="w", pady=(5, 4))
        row += 1

        self.wf_frame = ttk.LabelFrame(main, text="AI Model Workflows (select one or more)", padding=10)
        self.wf_frame.grid(row=row, column=0, columnspan=3, sticky="ew", pady=(0, 4))
        self.wf_frame.columnconfigure(0, weight=1)

        wf_row = 0
        ttk.Checkbutton(self.wf_frame, text="Portrait (BiRefNet-Portrait)",
                        variable=self.wf_portrait, style="Toolbutton").grid(row=wf_row, column=0, sticky="w")
        wf_row += 1
        ttk.Label(self.wf_frame, text="    Best for headshots and people. Exceptional hair and shoulder edge quality.",
                  font=("Helvetica", 9), foreground="gray").grid(row=wf_row, column=0, sticky="w")
        wf_row += 1

        ttk.Checkbutton(self.wf_frame, text="General Purpose (BiRefNet-General)",
                        variable=self.wf_general, style="Toolbutton").grid(row=wf_row, column=0, sticky="w", pady=(4, 0))
        wf_row += 1
        ttk.Label(self.wf_frame, text="    Best all-around model. Great for products, objects, and mixed content.",
                  font=("Helvetica", 9), foreground="gray").grid(row=wf_row, column=0, sticky="w")
        wf_row += 1

        ttk.Checkbutton(self.wf_frame, text="High Detail (BRIA RMBG)",
                        variable=self.wf_bria, style="Toolbutton").grid(row=wf_row, column=0, sticky="w", pady=(4, 0))
        wf_row += 1
        ttk.Label(self.wf_frame, text="    State-of-the-art by BRIA AI. Excels at complex scenes and fine textures.",
                  font=("Helvetica", 9), foreground="gray").grid(row=wf_row, column=0, sticky="w")
        self.wf_frame.grid_remove()
        row += 1

        self.bg_frame = ttk.LabelFrame(main, text="Background Options", padding=10)
        self.bg_frame.grid(row=row, column=0, columnspan=3, sticky="ew", pady=(0, 8))
        self.bg_frame.columnconfigure(1, weight=1)
        ttk.Label(self.bg_frame, text="Background:").grid(row=0, column=0, sticky="w", padx=(0, 8))
        bg_combo = ttk.Combobox(self.bg_frame, textvariable=self.bg_preset,
                                 values=list(self.BG_PRESETS.keys()), state="readonly", width=35)
        bg_combo.grid(row=0, column=1, sticky="w")
        bg_combo.bind("<<ComboboxSelected>>", self._on_bg_change)

        self.custom_bg_frame = ttk.Frame(self.bg_frame)
        self.custom_bg_frame.grid(row=1, column=0, columnspan=2, sticky="w", pady=(6, 0))
        ttk.Label(self.custom_bg_frame, text="Custom:").grid(row=0, column=0, padx=(0, 4))
        ttk.Entry(self.custom_bg_frame, textvariable=self.custom_bg, width=30).grid(row=0, column=1, padx=(0, 8))
        ttk.Label(self.custom_bg_frame, text='e.g. "#663399" or "#663399:#F77E2D:right"',
                  font=("Helvetica", 9)).grid(row=0, column=2)
        self.custom_bg_frame.grid_remove()
        self.bg_frame.grid_remove()
        row += 1

        self.bg_note = ttk.Label(main,
            text="Each AI model downloads on first use (~170-300 MB each). One-time per model.",
            font=("Helvetica", 9), foreground="gray")
        self.bg_note.grid(row=row, column=0, columnspan=3, sticky="w", pady=(0, 4))
        self.bg_note.grid_remove()
        row += 1

        ttk.Separator(main, orient="horizontal").grid(row=row, column=0, columnspan=3, sticky="ew", pady=8)
        row += 1

        self.process_btn = ttk.Button(main, text="Process Images", command=self._start_processing)
        self.process_btn.grid(row=row, column=0, columnspan=3, sticky="ew", pady=(8, 8), ipady=8)
        row += 1

        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(main, variable=self.progress_var, maximum=100, mode='determinate')
        self.progress_bar.grid(row=row, column=0, columnspan=3, sticky="ew", pady=(0, 4))
        row += 1

        self.status_label = ttk.Label(main, text="Ready", font=("Helvetica", 10))
        self.status_label.grid(row=row, column=0, columnspan=3, sticky="w")
        row += 1

        log_frame = ttk.LabelFrame(main, text="Log", padding=5)
        log_frame.grid(row=row, column=0, columnspan=3, sticky="nsew", pady=(8, 0))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        main.rowconfigure(row, weight=1)

        self.log_text = tk.Text(log_frame, height=8, state="disabled",
                                font=("Menlo" if sys.platform == "darwin" else "Consolas", 10),
                                bg="#F5F5F5", wrap="word")
        self.log_text.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.log_text.configure(yscrollcommand=scrollbar.set)

    def _browse_input(self):
        path = filedialog.askdirectory(title="Select folder containing images")
        if path:
            self.input_dir.set(path)
            if not self.output_dir.get():
                self.output_dir.set(str(Path(path) / "resized"))
            count = sum(1 for f in Path(path).iterdir()
                       if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS)
            self._log(f"Selected input: {path} ({count} images found)")

    def _browse_output(self):
        path = filedialog.askdirectory(title="Select output folder")
        if path:
            self.output_dir.set(path)

    def _on_size_change(self, event=None):
        if self.size_preset.get() == "Custom...":
            self.custom_size_frame.grid()
        else:
            self.custom_size_frame.grid_remove()

    def _on_bg_change(self, event=None):
        if self.bg_preset.get() == "Custom...":
            self.custom_bg_frame.grid()
        else:
            self.custom_bg_frame.grid_remove()

    def _toggle_bg_options(self):
        if self.remove_bg.get():
            self.wf_frame.grid()
            self.bg_frame.grid()
            self.bg_note.grid()
            if not any([self.wf_portrait.get(), self.wf_general.get(), self.wf_bria.get()]):
                self.wf_portrait.set(True)
        else:
            self.wf_frame.grid_remove()
            self.bg_frame.grid_remove()
            self.bg_note.grid_remove()

    def _log(self, msg):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", msg + "\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")
        self.root.update_idletasks()

    def _set_status(self, msg):
        self.status_label.configure(text=msg)
        self.root.update_idletasks()

    def _get_dimensions(self):
        if self.size_preset.get() == "Custom...":
            try:
                return int(self.custom_width.get()), int(self.custom_height.get())
            except ValueError:
                raise ValueError("Custom width and height must be numbers")
        return self.SIZE_PRESETS[self.size_preset.get()]

    def _get_bg_string(self):
        preset = self.bg_preset.get()
        if preset == "Custom...":
            return self.custom_bg.get()
        return self.BG_PRESETS[preset]

    def _validate(self):
        if not self.input_dir.get():
            messagebox.showerror("Missing Input", "Please select an input folder.")
            return False
        if not Path(self.input_dir.get()).is_dir():
            messagebox.showerror("Invalid Input", "The input folder does not exist.")
            return False
        if not self.output_dir.get():
            messagebox.showerror("Missing Output", "Please select an output folder.")
            return False
        try:
            w, h = self._get_dimensions()
            if w <= 0 or h <= 0:
                raise ValueError()
        except (ValueError, TypeError):
            messagebox.showerror("Invalid Size", "Width and height must be positive numbers.")
            return False
        return True

    def _start_processing(self):
        if self.is_processing:
            return
        if not self._validate():
            return
        self.is_processing = True
        self.process_btn.configure(state="disabled")
        self.progress_var.set(0)
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")
        thread = threading.Thread(target=self._process_thread, daemon=True)
        thread.start()

    def _get_selected_workflows(self):
        selected = []
        if self.wf_portrait.get():
            selected.append("portrait")
        if self.wf_general.get():
            selected.append("general")
        if self.wf_bria.get():
            selected.append("bria")
        return selected

    def _process_thread(self):
        try:
            input_path = Path(self.input_dir.get())
            output_base = Path(self.output_dir.get())
            width, height = self._get_dimensions()
            mode = self.crop_mode.get()
            fmt = self.output_format.get()
            quality = self.quality.get()
            do_remove_bg = self.remove_bg.get()

            bg_str = self._get_bg_string() if do_remove_bg else "#FFFFFF"
            bg_spec = parse_bg_spec(bg_str)

            keep_transparent = do_remove_bg and bg_spec['type'] == 'transparent'
            if keep_transparent and fmt == 'JPEG':
                fmt = 'PNG'
                self.root.after(0, lambda: self._log("JPEG does not support transparency. Switched to PNG."))

            if do_remove_bg:
                self.root.after(0, lambda: self._set_status("Checking AI models..."))
                try:
                    import rembg
                except ImportError:
                    self.root.after(0, lambda: messagebox.showerror(
                        "Missing Dependency",
                        "rembg is not installed.\n\n"
                        "Close this app and re-launch using:\n"
                        "  Mac: 'Launch Headshot Resizer.command'\n"
                        "  Win: 'Launch Headshot Resizer.bat'\n\n"
                        "The launcher will install all dependencies automatically."
                    ))
                    self.root.after(0, self._processing_done)
                    return

            images = sorted([
                f for f in input_path.iterdir()
                if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
            ])

            if not images:
                self.root.after(0, lambda: messagebox.showwarning("No Images", "No supported images found in the input folder."))
                self.root.after(0, self._processing_done)
                return

            total = len(images)

            if do_remove_bg:
                workflows = self._get_selected_workflows()
                if not workflows:
                    self.root.after(0, lambda: messagebox.showwarning(
                        "No Workflow Selected", "Please select at least one AI model workflow."))
                    self.root.after(0, self._processing_done)
                    return
            else:
                workflows = [None]

            total_runs = len(workflows)
            grand_processed = 0
            grand_errors = 0
            output_folders = []

            for run_idx, wf_key in enumerate(workflows):
                if wf_key:
                    wf = BG_WORKFLOWS[wf_key]
                    wf_label = wf["label"]
                    if total_runs > 1:
                        output_path = output_base / wf_key
                    else:
                        output_path = output_base
                    self.root.after(0, lambda lab=wf_label, r=run_idx:
                        self._log(f"\nWorkflow {r + 1}/{total_runs}: {lab}"))
                    self.root.after(0, lambda lab=wf_label:
                        self._set_status(f"Loading model: {lab}..."))
                else:
                    wf_label = "Resize Only"
                    output_path = output_base

                output_path.mkdir(parents=True, exist_ok=True)
                output_folders.append(str(output_path))

                bg_label = f" -> bg: {bg_str}" if wf_key else ""
                self.root.after(0, lambda t=total, w=width, h=height, m=mode, f=fmt, bl=bg_label:
                    self._log(f"Processing {t} images -> {w}x{h} ({m} crop, {f}){bl}\n"))

                processed = 0
                errors = 0

                for i, img_file in enumerate(images):
                    try:
                        name = img_file.name
                        if total_runs > 1:
                            status = f"[{wf_label}] {i + 1}/{total}: {name}"
                        else:
                            status = f"Processing {i + 1}/{total}: {name}"
                        self.root.after(0, lambda s=status: self._set_status(s))

                        img = Image.open(img_file)
                        orig_size = f"{img.width}x{img.height}"
                        img = fix_orientation(img)

                        if wf_key:
                            img = img.convert("RGBA")
                            img = remove_background(img, workflow_key=wf_key)
                            img = composite_on_background(img, bg_spec, width, height, crop_mode=mode)
                        else:
                            img = img.convert("RGB")
                            if mode == "center":
                                img = crop_center(img, width, height)
                            elif mode == "top":
                                img = crop_top(img, width, height)
                            elif mode == "fill":
                                img = fill_resize(img, width, height, bg_spec=bg_spec)

                        if fmt == "JPEG" and img.mode != "RGB":
                            img = img.convert("RGB")

                        ext = {"JPEG": ".jpg", "PNG": ".png", "WEBP": ".webp"}[fmt]
                        out_name = img_file.stem + ext
                        save_params = {}
                        if fmt == "JPEG":
                            save_params = {"quality": quality, "optimize": True}
                        elif fmt == "WEBP":
                            save_params = {"quality": quality}
                        elif fmt == "PNG":
                            save_params = {"optimize": True}

                        img.save(output_path / out_name, format=fmt, **save_params)
                        processed += 1

                        self.root.after(0, lambda n=name, s=orig_size, idx=i:
                            self._log(f"  OK [{idx + 1}/{total}] {n} ({s})"))

                    except Exception as e:
                        errors += 1
                        self.root.after(0, lambda n=img_file.name, err=str(e), idx=i:
                            self._log(f"  FAIL [{idx + 1}/{total}] {n}: {err}"))

                    overall = ((run_idx * total) + (i + 1)) / (total_runs * total) * 100
                    self.root.after(0, lambda p=overall: self.progress_var.set(p))

                grand_processed += processed
                grand_errors += errors

                self.root.after(0, lambda p=processed, e=errors, lab=wf_label:
                    self._log(f"\n  {lab}: {p} processed, {e} errors"))

            if total_runs > 1:
                self.root.after(0, lambda: self._log(
                    f"\nAll workflows complete: "
                    f"{grand_processed} total processed, {grand_errors} total errors\n"
                    f"Output folders: {', '.join(output_folders)}"))

            self.root.after(0, lambda gp=grand_processed:
                self._set_status(f"Complete -- {gp} images processed"))
            self.root.after(0, lambda: self._ask_open_folder(str(output_base)))

        except Exception as e:
            self.root.after(0, lambda: self._log(f"\nError: {e}"))
            self.root.after(0, lambda: self._set_status("Error -- see log"))
            self.root.after(0, lambda: messagebox.showerror("Processing Error", str(e)))
        finally:
            self.root.after(0, self._processing_done)

    def _processing_done(self):
        self.is_processing = False
        self.process_btn.configure(state="normal")

    def _ask_open_folder(self, path):
        if messagebox.askyesno("Complete", f"Processing complete!\n\nOpen output folder?"):
            if sys.platform == "darwin":
                subprocess.run(["open", path])
            elif sys.platform == "win32":
                os.startfile(path)
            else:
                subprocess.run(["xdg-open", path])


def main():
    root = tk.Tk()
    if sys.platform == "darwin":
        try:
            root.lift()
            root.attributes("-topmost", True)
            root.after(100, lambda: root.attributes("-topmost", False))
        except Exception:
            pass
    app = HeadshotResizerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

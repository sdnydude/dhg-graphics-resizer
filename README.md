# Digital Harmony Group Graphics Resizer V1.5

**Batch resize images to uniform dimensions with optional AI-powered background removal and replacement.**

A desktop GUI application built with Python/tkinter. No command line required — double-click to launch.

---

## Features

- **40+ size presets** organized by category: headshots, social media profiles, social media posts, banners, IAB digital ads, email, and web
- **3 crop modes**: Top (best for headshots), Center, Fill (no crop with padding)
- **AI background removal** with 3 selectable models:
  - 🎯 **Portrait** (BiRefNet-Portrait) — Best for headshots and people
  - 🌐 **General Purpose** (BiRefNet-General) — Best all-around model
  - ✨ **High Detail** (BRIA RMBG) — State-of-the-art for complex scenes
- **Background replacement** with solid colors, multi-stop gradients, radial gradients, or transparency
- **Brand presets**: NACE Brand Gradient, ONA Teal, ONA Summit Gradient
- **Multi-workflow comparison**: Select multiple AI models and outputs are organized into subfolders
- **Export**: JPEG (with quality control), PNG, WebP
- **Zero-config setup**: Launchers auto-create virtual environments and install dependencies

## Quick Start

### Mac

1. Download the `mac/` folder
2. Double-click `Launch Headshot Resizer.command`
3. First run installs dependencies automatically (~60 seconds)

> If macOS blocks it: Right-click → Open → Open
>
> If tkinter is missing: the app shows the exact `brew install` command with a Copy button

### Windows

1. Install Python 3.9+ from [python.org](https://www.python.org/downloads/) — **check "Add Python to PATH"**
2. Download the `windows/` folder
3. Double-click `Launch Headshot Resizer.bat`
4. First run installs dependencies automatically (~60 seconds)

## Size Presets

| Category | Examples |
|----------|----------|
| Headshots & Avatars | 200×200, 300×300, 400×400, 500×500, 800×800 |
| Social Media Profiles | Facebook 170×170, Instagram 320×320, LinkedIn 400×400, YouTube 800×800 |
| Social Media Posts | Instagram Square 1080×1080, Story 1080×1920, Facebook 1200×630, Pinterest 1000×1500 |
| Banners & Headers | Facebook Cover 820×312, X Header 1500×500, LinkedIn Banner 1584×396 |
| Digital Ads (IAB) | Medium Rectangle 300×250, Leaderboard 728×90, Billboard 970×250 |
| Email & Web | Email Header 600×200, Hero Banner 1200×400, Full HD 1920×1080 |
| Custom | Any width × height |

## Background Replacement

When AI background removal is enabled, replace with:

- **Solid colors**: White, grays, or any hex color
- **Gradients**: Corporate Blue, NACE Brand, ONA Summit, or custom
- **Transparent**: Auto-switches to PNG output

### Custom Gradient Syntax

```
#663399                → Solid color
#663399:#F77E2D        → Top-to-bottom gradient
#663399:#F77E2D:right  → Left-to-right gradient
#32374A:#663399:#F77E2D → 3-stop gradient
#663399:#F77E2D:radial  → Radial gradient
#663399:#F77E2D:diagonal → Diagonal gradient
```

## Project Structure

```
dhg-graphics-resizer/
├── batch_resize_headshots.py        # Main application (~1000 lines)
├── requirements.txt                 # Python dependencies
├── mac/
│   ├── batch_resize_headshots.py    # App (included for standalone use)
│   ├── Launch Headshot Resizer.command
│   └── README.md
├── windows/
│   ├── batch_resize_headshots.py    # App (included for standalone use)
│   ├── Launch Headshot Resizer.bat
│   └── README.md
├── docs/
│   └── DHG-Graphics-Resizer-User-Guide.docx
├── CHANGELOG.md
├── LICENSE                          # MIT
└── README.md
```

## Requirements

- Python 3.9+
- tkinter (usually included; on Mac with Homebrew: `brew install python-tk@3.xx`)
- Dependencies (auto-installed by launchers):
  - Pillow — image processing
  - rembg — AI background removal
  - onnxruntime — model inference

## Built By

**Digital Harmony Group** — [digitalharmonygroup.com](https://digitalharmonygroup.com)

Contact: Stephen Webber

# Digital Harmony Group Graphics Resizer V1.5 — Mac

Resize batches of images to uniform dimensions. No command line needed.

## Setup (One Time)

### 1. Python should already be installed
Most Macs have Python via Homebrew or Xcode tools. If not:
- Download from https://www.python.org/downloads/

### 2. Launch
**Double-click `Launch Headshot Resizer.command`**

First time it runs:
- If macOS blocks it → Right-click → Open → Open
- If it says "tkinter missing" → it will show you the exact brew command to run, with a Copy button
- It creates a `.venv` folder and installs all dependencies (~60 seconds, one-time)
- After that, launches instantly

## How to Use

1. **Input Folder** — Click Browse, select the folder with your photos
2. **Output Folder** — Auto-fills to a "resized" subfolder, or choose your own
3. **Size** — Default 500×500, or pick a preset / enter custom
4. **Crop Mode:**
   - **Top** — Best for headshots (keeps the top of the head)
   - **Center** — Center crop
   - **Fill** — No cropping, fits image with padding
5. **Background Removal** (optional) — Check the box to enable AI background removal with color/gradient replacement
6. Click **Process Images**
7. Opens the output folder when done

## Troubleshooting

| Problem | Fix |
|---------|-----|
| "unidentified developer" | Right-click the .command file → Open → Open |
| "tkinter missing" | Run the `brew install python-tk@X.XX` command shown in the popup |
| Tops of heads cut off | Switch crop mode to **Top** |
| Background removal slow | Normal — ~2-5 seconds per image for AI processing |
| Need to reinstall deps | Delete the `.venv` folder and re-launch |

## What's in the Folder

| File | Purpose |
|------|---------|
| `Launch Headshot Resizer.command` | Double-click this to launch |
| `batch_resize_headshots.py` | The app (don't edit) |
| `.venv/` | Created on first run — dependencies live here |

Questions? Contact Stephen Webber — DHG

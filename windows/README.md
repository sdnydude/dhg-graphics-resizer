# Digital Harmony Group Graphics Resizer V1.5 — Windows

Resize batches of images to uniform dimensions. No command line needed.

## Setup (One Time)

### 1. Install Python
- Download from https://www.python.org/downloads/
- ⚠️ **CHECK THE BOX** that says **"Add Python to PATH"** during installation
- Restart your computer after installing

### 2. Launch
**Double-click `Launch Headshot Resizer.bat`**

First time it runs:
- Creates a `.venv` folder and installs all dependencies (~60 seconds, one-time)
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
| "Python is not installed" | Install from python.org — check "Add to PATH" |
| Window flashes and closes | Python isn't in PATH — reinstall and check the PATH box |
| Tops of heads cut off | Switch crop mode to **Top** |
| Background removal slow | Normal — ~2-5 seconds per image for AI processing |
| Need to reinstall deps | Delete the `.venv` folder and re-launch |

Questions? Contact Stephen Webber — DHG

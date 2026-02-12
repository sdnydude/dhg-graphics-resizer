#!/bin/bash
# ============================================================
# DHG Graphics Resizer — macOS
# Double-click in Finder to launch.
#
# First run: checks tkinter, creates .venv, installs all deps.
# Subsequent runs: launches instantly.
# ============================================================

cd "$(dirname "$0")"
VENV_DIR=".venv"
DEPS_INSTALLED=".venv/.deps_installed"

# --- Find Python 3 ---
PYTHON=""
for p in python3 /opt/homebrew/bin/python3 /usr/local/bin/python3 /usr/bin/python3; do
    if command -v "$p" &>/dev/null; then
        PYTHON="$p"
        break
    fi
done

if [ -z "$PYTHON" ]; then
    osascript -e 'display dialog "Python 3 is not installed.\n\nInstall from python.org or run:\n  brew install python3" with title "DHG Graphics Resizer" buttons {"OK"} default button "OK" with icon stop'
    exit 1
fi

PY_VER=$("$PYTHON" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "Python: $PYTHON ($PY_VER)"

# --- Check tkinter ---
if ! "$PYTHON" -c "import tkinter" 2>/dev/null; then
    BREW_CMD="brew install python-tk@${PY_VER}"
    echo ""
    echo "⚠️  tkinter is missing. Run this in Terminal first:"
    echo "    $BREW_CMD"
    echo ""
    osascript -e "display dialog \"tkinter is required but not installed.\n\nOpen Terminal and run:\n\n    ${BREW_CMD}\n\nThen double-click this launcher again.\" with title \"DHG Graphics Resizer\" buttons {\"Copy Command\", \"OK\"} default button \"OK\" with icon caution" \
        -e 'if button returned of result is "Copy Command" then
            set the clipboard to "'"$BREW_CMD"'"
            display dialog "Copied! Paste it in Terminal." buttons {"OK"} default button "OK"
        end if'
    exit 1
fi

# --- Create venv on first run ---
if [ ! -d "$VENV_DIR" ]; then
    echo ""
    echo "╔══════════════════════════════════════════════════════╗"
    echo "║  First run — setting up environment (~60 seconds)    ║"
    echo "╚══════════════════════════════════════════════════════╝"
    echo ""
    echo "Creating virtual environment..."
    "$PYTHON" -m venv "$VENV_DIR"
    if [ $? -ne 0 ]; then
        echo "❌ Failed to create venv."
        read -p "Press Enter to close..."
        exit 1
    fi
fi

# --- Install dependencies if not yet done ---
if [ ! -f "$DEPS_INSTALLED" ]; then
    echo "Installing dependencies (one-time)..."
    "$VENV_DIR/bin/pip" install --quiet --upgrade pip

    echo "  → Pillow (image processing)..."
    "$VENV_DIR/bin/pip" install --quiet Pillow

    echo "  → rembg (AI background removal)..."
    "$VENV_DIR/bin/pip" install --quiet rembg onnxruntime

    if [ $? -ne 0 ]; then
        echo "❌ Dependency install failed."
        read -p "Press Enter to close..."
        exit 1
    fi

    # Mark deps as installed so we skip next time
    date > "$DEPS_INSTALLED"
    echo ""
    echo "✅ Setup complete!"
    echo ""
fi

# --- Launch ---
"$VENV_DIR/bin/python" batch_resize_headshots.py

if [ $? -ne 0 ]; then
    echo ""
    read -p "Press Enter to close..."
fi

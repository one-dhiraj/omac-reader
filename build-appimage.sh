#!/usr/bin/env bash
set -Eeuo pipefail

# OMAC Reader AppImage build script

PROJECT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
VENV_PYTHON="$PROJECT_DIR/.venv/bin/python"
TOOLS_DIR="$HOME/Tools/linuxdeploy"
LINUXDEPLOY="$TOOLS_DIR/linuxdeploy-x86_64.AppImage"
APPIMAGE_PLUGIN="$TOOLS_DIR/linuxdeploy-plugin-appimage-x86_64.AppImage"
APPDIR="$PROJECT_DIR/AppDir"
RELEASE_DIR="$PROJECT_DIR/release"

echo "=================================="
echo " Building OMAC Reader AppImage"
echo "=================================="

# Check project prerequisites
if [[ ! -x "$VENV_PYTHON" ]]; then
    echo "ERROR: Project virtual environment not found."
    echo "Expected: $VENV_PYTHON"
    exit 1
fi

if [[ ! -f "$PROJECT_DIR/main.py" ]]; then
    echo "ERROR: main.py not found."
    exit 1
fi

if [[ ! -f "$PROJECT_DIR/assets/omac-reader.png" ]]; then
    echo "ERROR: Application icon not found."
    exit 1
fi

command -v curl >/dev/null || {
    echo "ERROR: curl is required."
    exit 1
}

# Ensure packaging tools are available
mkdir -p "$TOOLS_DIR"

if [[ ! -x "$LINUXDEPLOY" ]]; then
    echo "Downloading linuxdeploy..."
    curl -fL --retry 3 \
        "https://github.com/linuxdeploy/linuxdeploy/releases/download/continuous/linuxdeploy-x86_64.AppImage" \
        -o "$LINUXDEPLOY"
    chmod +x "$LINUXDEPLOY"
fi

if [[ ! -x "$APPIMAGE_PLUGIN" ]]; then
    echo "Downloading AppImage output plugin..."
    curl -fL --retry 3 \
        "https://github.com/linuxdeploy/linuxdeploy-plugin-appimage/releases/download/continuous/linuxdeploy-plugin-appimage-x86_64.AppImage" \
        -o "$APPIMAGE_PLUGIN"
    chmod +x "$APPIMAGE_PLUGIN"
fi

# Step 1: Build the PyInstaller application bundle
echo
echo "[1/4] Building application bundle..."

cd "$PROJECT_DIR"

"$VENV_PYTHON" -m PyInstaller \
    --noconfirm \
    --clean \
    --windowed \
    --name "OMAC Reader" \
    --icon assets/omac-reader.png \
    --add-data "assets:assets" \
    main.py

BUNDLE="$PROJECT_DIR/dist/OMAC Reader"

if [[ ! -f "$BUNDLE/OMAC Reader" ]]; then
    echo "ERROR: PyInstaller did not produce the expected executable."
    exit 1
fi

# Step 2: Prepare a fresh AppDir
echo
echo "[2/4] Preparing AppDir..."

rm -rf "$APPDIR"
mkdir -p "$APPDIR/usr/bin"

cp -a "$BUNDLE/." "$APPDIR/usr/bin/"
mv "$APPDIR/usr/bin/OMAC Reader" "$APPDIR/usr/bin/omac-reader"

mkdir -p "$APPDIR/usr/share/icons/hicolor/256x256/apps"
cp "$PROJECT_DIR/assets/omac-reader.png" "$APPDIR/usr/share/icons/hicolor/256x256/apps/omac-reader.png"
cp "$PROJECT_DIR/assets/omac-reader.png" "$APPDIR/omac-reader.png"

cp "$PROJECT_DIR/LICENSE" "$APPDIR/LICENSE"
cp "$PROJECT_DIR/README.md" "$APPDIR/README.md"

cat > "$APPDIR/omac-reader.desktop" <<'DESKTOP'
[Desktop Entry]
Type=Application
Name=OMAC Reader
Comment=One More Amazing Comic Reader
Exec=omac-reader
Icon=omac-reader
Categories=Graphics;Viewer;
Terminal=false
DESKTOP

# Step 3: Generate the AppImage
echo
echo "[3/4] Generating AppImage..."

mkdir -p "$RELEASE_DIR"
rm -f "$RELEASE_DIR/OMAC_Reader-x86_64.AppImage"

export PATH="$TOOLS_DIR:$PATH"

cd "$RELEASE_DIR"

"$LINUXDEPLOY" \
    --appdir "$APPDIR" \
    --desktop-file "$APPDIR/omac-reader.desktop" \
    --icon-file "$APPDIR/omac-reader.png" \
    --output appimage

# Step 4: Report the result
echo
echo "[4/4] Build finished."

shopt -s nullglob
OUTPUTS=("$RELEASE_DIR"/*.AppImage)

if (( ${#OUTPUTS[@]} == 0 )); then
    echo "ERROR: No AppImage was found in $RELEASE_DIR"
    exit 1
fi

echo
echo "AppImage output:"
for file in "${OUTPUTS[@]}"; do
    ls -lh "$file"
    echo "Path: $file"
done

if command -v unar >/dev/null 2>&1; then
    echo
    echo "NOTE: CBR support depends on the external unar utility."
    echo "The current build script does not bundle unar."
fi

echo
echo "Build complete. Test the AppImage before distributing it."

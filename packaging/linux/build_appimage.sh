#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
BUILD_ROOT="$PROJECT_DIR/build/linux"
PYINSTALLER_WORK="$PROJECT_DIR/build/pyinstaller-linux"
DIST_DIR="$PROJECT_DIR/dist"
APPDIR="$BUILD_ROOT/U1FA.AppDir"
APP_NAME="U1 Filament Automation"
ARCH="${U1FA_ARCH:-x86_64}"
APPIMAGETOOL="${APPIMAGETOOL:-}"
VERSION="$(cd "$PROJECT_DIR" && PYTHONPATH="$PROJECT_DIR/src" python3 -c 'from u1_filament_automation import __version__; print(__version__)')"

if [ "$ARCH" != "x86_64" ]; then
    printf 'Architettura Linux non supportata in questa beta: %s\n' "$ARCH" >&2
    exit 2
fi
if [ -z "$APPIMAGETOOL" ] || [ ! -x "$APPIMAGETOOL" ]; then
    printf 'Impostare APPIMAGETOOL sul percorso eseguibile di appimagetool.\n' >&2
    exit 2
fi

rm -rf "$BUILD_ROOT" "$PYINSTALLER_WORK" "$DIST_DIR/$APP_NAME"
mkdir -p "$BUILD_ROOT" "$DIST_DIR"

cd "$PROJECT_DIR"
python3 -m PyInstaller \
    --noconfirm \
    --clean \
    --windowed \
    --onedir \
    --name "$APP_NAME" \
    --add-data "$PROJECT_DIR/src/u1_filament_automation/assets/u1fa_logo.png:u1_filament_automation/assets" \
    --add-data "$PROJECT_DIR/src/u1_filament_automation/assets/flow_calibrator_stock.py:u1_filament_automation/assets" \
    --add-data "$PROJECT_DIR/src/u1_filament_automation/assets/flow_calibrator_v6.py:u1_filament_automation/assets" \
    --add-data "$PROJECT_DIR/src/u1_filament_automation/assets/adaptive_pa_macro.cfg:u1_filament_automation/assets" \
    --workpath "$PYINSTALLER_WORK" \
    --specpath "$BUILD_ROOT" \
    --distpath "$DIST_DIR" \
    "$SCRIPT_DIR/u1fa_bootstrap.py"

mkdir -p "$APPDIR/usr/lib/u1fa" "$APPDIR/usr/share/applications" \
    "$APPDIR/usr/share/icons/hicolor/512x512/apps"
cp -R "$DIST_DIR/$APP_NAME/." "$APPDIR/usr/lib/u1fa/"
cp "$PROJECT_DIR/src/u1_filament_automation/assets/u1fa_logo.png" \
    "$APPDIR/u1-filament-automation.png"
cp "$PROJECT_DIR/src/u1_filament_automation/assets/u1fa_logo.png" \
    "$APPDIR/usr/share/icons/hicolor/512x512/apps/u1-filament-automation.png"

cat > "$APPDIR/AppRun" <<'EOF'
#!/bin/sh
APPDIR_PATH="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
exec "$APPDIR_PATH/usr/lib/u1fa/U1 Filament Automation" "$@"
EOF
chmod 0755 "$APPDIR/AppRun"

cat > "$APPDIR/u1-filament-automation.desktop" <<'EOF'
[Desktop Entry]
Type=Application
Name=U1 Filament Automation
Comment=Spoolman, Snapmaker Orca and Adaptive PA automation for Snapmaker U1
Exec=u1-filament-automation
Icon=u1-filament-automation
Categories=Utility;
Terminal=false
EOF
cp "$APPDIR/u1-filament-automation.desktop" "$APPDIR/usr/share/applications/"

OUTPUT="$DIST_DIR/U1-Filament-Automation-v${VERSION}-Linux-${ARCH}.AppImage"
rm -f "$OUTPUT"
ARCH="$ARCH" APPIMAGE_EXTRACT_AND_RUN=1 "$APPIMAGETOOL" "$APPDIR" "$OUTPUT"
chmod 0755 "$OUTPUT"
sha256sum "$OUTPUT"
printf 'AppImage creata: %s\n' "$OUTPUT"

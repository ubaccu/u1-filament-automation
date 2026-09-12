#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
BUILD_ROOT="$PROJECT_DIR/build/macos"
DIST_DIR="$PROJECT_DIR/dist"
ICONSET="$BUILD_ROOT/U1FA.iconset"
ICON_FILE="$BUILD_ROOT/U1FA.icns"
APP_NAME="U1 Filament Automation"
ARCH="${U1FA_ARCH:-$(uname -m)}"
VERSION="$(cd "$PROJECT_DIR" && PYTHONPATH="$PROJECT_DIR/src" python3 -c 'from u1_filament_automation import __version__; print(__version__)')"
SHORT_VERSION="${VERSION%%[!0-9.]*}"
BUNDLE_VERSION="${VERSION//[^0-9]/}"

case "$ARCH" in
    x86_64|arm64) ;;
    *)
        printf 'Architettura macOS non supportata: %s\n' "$ARCH" >&2
        exit 2
        ;;
esac

if [ "$ARCH" = "arm64" ]; then
    export MACOSX_DEPLOYMENT_TARGET="${MACOSX_DEPLOYMENT_TARGET:-11.0}"
else
    export MACOSX_DEPLOYMENT_TARGET="${MACOSX_DEPLOYMENT_TARGET:-10.15}"
fi

rm -rf "$BUILD_ROOT" "$PROJECT_DIR/build/pyinstaller" "$DIST_DIR/$APP_NAME.app"
mkdir -p "$ICONSET" "$DIST_DIR"

SOURCE_ICON="$PROJECT_DIR/src/u1_filament_automation/assets/u1fa_logo.png"
PRODUCT_IMAGE="$PROJECT_DIR/src/u1_filament_automation/assets/snapmaker_u1_official.webp"
PRODUCT_IMAGE_ARGS=()
if [ -f "$PRODUCT_IMAGE" ]; then
    PRODUCT_IMAGE_ARGS=(--add-data "$PRODUCT_IMAGE:u1_filament_automation/assets")
fi

for size in 16 32 128 256 512; do
    /usr/bin/sips -z "$size" "$size" "$SOURCE_ICON" \
        --out "$ICONSET/icon_${size}x${size}.png" >/dev/null
    double="$((size * 2))"
    /usr/bin/sips -z "$double" "$double" "$SOURCE_ICON" \
        --out "$ICONSET/icon_${size}x${size}@2x.png" >/dev/null
done
/usr/bin/iconutil -c icns "$ICONSET" -o "$ICON_FILE"

cd "$PROJECT_DIR"
python3 -m PyInstaller \
    --noconfirm \
    --clean \
    --windowed \
    --name "$APP_NAME" \
    --icon "$ICON_FILE" \
    --target-architecture "$ARCH" \
    --osx-bundle-identifier com.bottega3dlab.u1fa \
    --collect-data certifi \
    --add-data "$PROJECT_DIR/src/u1_filament_automation/assets/u1fa_logo.png:u1_filament_automation/assets" \
    --add-data "$PROJECT_DIR/src/u1_filament_automation/assets/flow_calibrator_stock.py:u1_filament_automation/assets" \
    --add-data "$PROJECT_DIR/src/u1_filament_automation/assets/flow_calibrator_v6.py:u1_filament_automation/assets" \
    --add-data "$PROJECT_DIR/src/u1_filament_automation/assets/adaptive_pa_macro.cfg:u1_filament_automation/assets" \
    "${PRODUCT_IMAGE_ARGS[@]}" \
    --workpath "$PROJECT_DIR/build/pyinstaller" \
    --specpath "$BUILD_ROOT" \
    --distpath "$DIST_DIR" \
    "$PROJECT_DIR/packaging/macos/u1fa_bootstrap.py"

U1FA_DESKTOP_SELFTEST=1 \
    "$DIST_DIR/$APP_NAME.app/Contents/MacOS/$APP_NAME"

PLIST="$DIST_DIR/$APP_NAME.app/Contents/Info.plist"
/usr/libexec/PlistBuddy -c "Add :CFBundleShortVersionString string $SHORT_VERSION" "$PLIST" 2>/dev/null || \
    /usr/libexec/PlistBuddy -c "Set :CFBundleShortVersionString $SHORT_VERSION" "$PLIST"
/usr/libexec/PlistBuddy -c "Add :CFBundleVersion string $BUNDLE_VERSION" "$PLIST" 2>/dev/null || \
    /usr/libexec/PlistBuddy -c "Set :CFBundleVersion $BUNDLE_VERSION" "$PLIST"
/usr/libexec/PlistBuddy -c "Add :LSUIElement bool false" "$PLIST" 2>/dev/null || \
    /usr/libexec/PlistBuddy -c "Set :LSUIElement false" "$PLIST"
/usr/libexec/PlistBuddy -c "Add :LSMinimumSystemVersion string $MACOSX_DEPLOYMENT_TARGET" "$PLIST" 2>/dev/null || \
    /usr/libexec/PlistBuddy -c "Set :LSMinimumSystemVersion $MACOSX_DEPLOYMENT_TARGET" "$PLIST"

# Firma ad-hoc: sufficiente per verificare l'integrità della build. Per eliminare
# gli avvisi Gatekeeper serviranno Developer ID e notarizzazione Apple.
/usr/bin/codesign --force --deep --sign - "$DIST_DIR/$APP_NAME.app"
/usr/bin/codesign --verify --deep --strict "$DIST_DIR/$APP_NAME.app"

STAGE="$BUILD_ROOT/dmg-stage"
README_IT_SOURCE="$PROJECT_DIR/packaging/macos/README_FIRST_macOS.html"
README_EN_SOURCE="$PROJECT_DIR/packaging/macos/README_FIRST_macOS_EN.html"
README_IT_DMG_NAME="LEGGIMI PRIMA - macOS.html"
README_EN_DMG_NAME="README FIRST - macOS.html"
rm -rf "$STAGE"
mkdir -p "$STAGE"
cp -R "$DIST_DIR/$APP_NAME.app" "$STAGE/"
ln -s /Applications "$STAGE/Applications"
test -f "$README_IT_SOURCE"
test -f "$README_EN_SOURCE"
cp "$README_IT_SOURCE" "$STAGE/$README_IT_DMG_NAME"
cp "$README_EN_SOURCE" "$STAGE/$README_EN_DMG_NAME"

DMG_NAME="U1-Filament-Automation-v${VERSION}-macOS-${ARCH}.dmg"
DMG_PATH="$DIST_DIR/$DMG_NAME"
rm -f "$DMG_PATH"
/usr/bin/hdiutil create \
    -volname "U1 Filament Automation" \
    -srcfolder "$STAGE" \
    -ov \
    -format UDZO \
    "$DMG_PATH"

/usr/bin/shasum -a 256 "$DMG_PATH"
printf 'DMG creato: %s\n' "$DMG_PATH"

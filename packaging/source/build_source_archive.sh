#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

OUT_DIR="${1:-dist}"
mkdir -p "$OUT_DIR"
OUT_DIR="$(cd "$OUT_DIR" && pwd)"

VERSION="$(sed -n 's/^version = "\([^"]*\)"/\1/p' pyproject.toml | head -n 1)"
if [[ -z "$VERSION" ]]; then
  echo "Unable to read project version from pyproject.toml" >&2
  exit 1
fi

COMMIT="$(git rev-parse HEAD)"
PREFIX="U1-Filament-Automation-v${VERSION}-Source"
ARCHIVE="${OUT_DIR}/${PREFIX}.zip"
STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT
mkdir -p "$STAGE/$PREFIX"

# Corresponding source for the distributed desktop build. Development-only
# workflow files, Copilot instructions, tests, roadmaps and private CI metadata
# are intentionally not part of the public source package.
ITEMS=(
  "src/u1_filament_automation"
  "packaging"
  "vendor"
  "pyproject.toml"
  "LICENSE"
  "THIRD_PARTY_NOTICES.md"
  "README.md"
  "README.it.md"
  "SUPPORT.md"
  "SUPPORT.it.md"
  "SECURITY.md"
  "CHANGELOG.md"
  "docs/README.md"
  "docs/README.it.md"
  "docs/AGGIORNAMENTI_APP.md"
  "docs/APP_UPDATES.md"
  "docs/FIRMWARE_COMPATIBILITY.md"
  "docs/COMPATIBILITA_FIRMWARE.md"
  "docs/INSTALLAZIONE_STAMPANTE.md"
  "docs/PRINTER_SETUP.md"
)

for item in "${ITEMS[@]}"; do
  if [[ ! -e "$item" ]]; then
    echo "Required source-release item missing: $item" >&2
    exit 1
  fi
  mkdir -p "$STAGE/$PREFIX/$(dirname "$item")"
  cp -a "$item" "$STAGE/$PREFIX/$item"
done

cat > "$STAGE/$PREFIX/SOURCE_RELEASE_INFO.txt" <<EOF
U1 Filament Automation (U1FA)
Version: ${VERSION}
Build commit: ${COMMIT}
Public release repository: ubaccu/u1-filament-automation
License: GNU GPLv3; see LICENSE and THIRD_PARTY_NOTICES.md

This archive contains the source code and build/packaging scripts corresponding
to the distributed desktop release. Development-only CI configuration, tests,
Copilot instructions and unpublished planning material are not required to use,
modify or rebuild the distributed program and are not included here.
EOF

rm -f "$ARCHIVE"
(
  cd "$STAGE"
  zip -q -r "$ARCHIVE" "$PREFIX"
)

sha256sum "$ARCHIVE"
echo "$ARCHIVE"

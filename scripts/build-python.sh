#!/bin/bash
set -e

PYTHON_VERSION="3.11.7"
RELEASE_TAG="20240107"
DIST_DIR="python/portable"
BASE_URL="https://github.com/indygreg/python-build-standalone/releases/download/${RELEASE_TAG}"

if [ -f "$DIST_DIR/bin/python3" ]; then
  echo "[build-python] Portable Python already exists at $DIST_DIR"
  exit 0
fi

echo "[build-python] Preparing portable Python environment..."

ARCH="aarch64"
case $(uname -m) in
  x86_64) ARCH="x86_64" ;;
esac

ARCHIVE="cpython-${PYTHON_VERSION}+${RELEASE_TAG}-${ARCH}-apple-darwin-pgo+lto-full.tar.zst"
DOWNLOAD_URL="${BASE_URL}/${ARCHIVE}"

mkdir -p "$DIST_DIR"

echo "[build-python] Downloading $ARCHIVE ..."

# Install zstandard if needed
python3 -c "import zstandard" 2>/dev/null || pip install zstandard

# Download to temp file
TMP_FILE=$(mktemp)
trap "rm -f $TMP_FILE" EXIT

curl -fL "$DOWNLOAD_URL" -o "$TMP_FILE"

echo "[build-python] Extracting..."
python3 -c "
import zstandard, tarfile, os, sys, shutil

src = '$TMP_FILE'
dst = '$DIST_DIR'

TMP_EXTRACT = dst + '_tmp'
os.makedirs(TMP_EXTRACT, exist_ok=True)

dctx = zstandard.ZstdDecompressor()
with open(src, 'rb') as f:
    with dctx.stream_reader(f) as reader:
        tar = tarfile.open(fileobj=reader, mode='r|')
        tar.extractall(path=TMP_EXTRACT)
        tar.close()

# Find the actual install directory (python/install/)
for root, dirs, files in os.walk(TMP_EXTRACT):
    if 'bin' in dirs and 'lib' in dirs:
        for item in os.listdir(root):
            s = os.path.join(root, item)
            d = os.path.join(dst, item)
            if os.path.isdir(s):
                shutil.copytree(s, d, symlinks=True, dirs_exist_ok=True)
            else:
                shutil.copy2(s, d)
        break
shutil.rmtree(TMP_EXTRACT, ignore_errors=True)
print('Extraction complete')
"

echo "[build-python] Installing Python dependencies..."
PYTHON_BIN="$DIST_DIR/bin/python3"
if [ ! -f "$PYTHON_BIN" ]; then
  PYTHON_BIN="$DIST_DIR/bin/python3.11"
fi
"$PYTHON_BIN" -m pip install --no-input -r python/requirements.txt

echo "[build-python] Stripping unnecessary files..."
bash "$(dirname "$0")/strip-python.sh" "$DIST_DIR"

echo "[build-python] Portable Python ready at $DIST_DIR"

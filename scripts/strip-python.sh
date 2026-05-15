#!/bin/bash
# Strip unnecessary files from portable Python to reduce app size.
# Run after pip install, before electron-builder packaging.

set -e
DIR="$1"

if [ -z "$DIR" ]; then
  echo "Usage: $0 <python-portable-dir>"
  exit 1
fi

echo "[strip-python] Cleaning $DIR ..."

# 1. Python stdlib test suite (~28MB)
rm -rf "$DIR/lib/python3.11/test"
rm -rf "$DIR/lib/python3.11/idlelib"
rm -rf "$DIR/lib/python3.11/tkinter"
rm -rf "$DIR/lib/python3.11/turtledemo"
rm -rf "$DIR/lib/python3.11/curses"
rm -rf "$DIR/lib/python3.11/lib2to3/tests"

# 2. pip cache, setuptools unused files
rm -rf "$DIR/lib/python3.11/site-packages/setuptools/_vendor"
rm -rf "$DIR/lib/python3.11/lib2to3"
rm -rf "$DIR/lib/python3.11/ensurepip"

# 3. Python config files (keep config for ctypes etc.)
rm -rf "$DIR/lib/pkgconfig"
rm -rf "$DIR/share"

# 4. pip, setuptools, pkg_resources (not needed at runtime, ~12MB)
rm -rf "$DIR/lib/python3.11/site-packages/pip"
rm -rf "$DIR/lib/python3.11/site-packages/setuptools"
rm -rf "$DIR/lib/python3.11/site-packages/pkg_resources"
rm -rf "$DIR/lib/python3.11/site-packages/distlib"

# 5. Static libraries (.a)
find "$DIR" -name '*.a' -not -path '*/test/*' -delete

# 6. Cython source files
find "$DIR" -name '*.pxd' -delete
find "$DIR" -name '*.pxi' -delete

# 7. All __pycache__ and .pyc
find "$DIR" -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true
find "$DIR" -name '*.pyc' -delete

# 8. Numpy test data (~20MB)
find "$DIR"/lib/python3.11/site-packages/numpy -type d -name 'tests' -exec rm -rf {} + 2>/dev/null || true
find "$DIR"/lib/python3.11/site-packages/numpy -type d -name 'f2py' -exec rm -rf {} + 2>/dev/null || true

# 9. Pandas test data (~15MB)
find "$DIR"/lib/python3.11/site-packages/pandas -type d -name 'tests' -not -path '*_testing*' -exec rm -rf {} + 2>/dev/null || true

# 10. Matplotlib sample data + tests (~10MB)
rm -rf "$DIR"/lib/python3.11/site-packages/matplotlib/tests
rm -rf "$DIR"/lib/python3.11/site-packages/matplotlib/sample_data
rm -rf "$DIR"/lib/python3.11/site-packages/mpl_toolkits/tests

# 11. Remove interactive-only matplotlib backends (GTK, Qt, WX, Tk, MacOSX)
for b in gtk qt wx tk macosx; do
  find "$DIR"/lib/python3.11/site-packages/matplotlib -name "backend_${b}*" -delete 2>/dev/null || true
done

# 12. Strip PIL test images + ImageShow (~5MB)
rm -rf "$DIR"/lib/python3.11/site-packages/PIL/ImageShow.py
find "$DIR"/lib/python3.11/site-packages/PIL -name '*.dll' -delete 2>/dev/null || true
find "$DIR"/lib/python3.11/site-packages/PIL -name '*.so' -size +2M -delete 2>/dev/null || true

# 13. .c and .cpp source files in site-packages
find "$DIR"/lib/python3.11/site-packages -name '*.c' -delete 2>/dev/null || true
find "$DIR"/lib/python3.11/site-packages -name '*.cpp' -delete 2>/dev/null || true

# 15. Documentation
find "$DIR" -type f -name '*.rst' -delete 2>/dev/null || true
find "$DIR" -type f -name '*.txt' -not -name 'requirements.txt' -delete 2>/dev/null || true

# 16. Include headers
rm -rf "$DIR/include"

echo "[strip-python] Cleanup complete"
du -sh "$DIR"

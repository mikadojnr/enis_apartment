#!/bin/bash

# Create zip file of entire project
PROJECT_ROOT="/vercel/share/v0-project"
DIST_DIR="$PROJECT_ROOT/dist"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
ZIP_FILE="$DIST_DIR/eni-apartments-complete-$TIMESTAMP.zip"

# Create dist directory
mkdir -p "$DIST_DIR"

echo "[v0] Creating zip file: $ZIP_FILE"
echo "[v0] Project root: $PROJECT_ROOT"

# Navigate to parent directory and create zip
cd "$(dirname "$PROJECT_ROOT")"

# Create zip, excluding unnecessary files
zip -r "$ZIP_FILE" \
  "v0-project" \
  -x \
  "v0-project/.git/*" \
  "v0-project/.env.local" \
  "v0-project/__pycache__/*" \
  "v0-project/.pytest_cache/*" \
  "v0-project/.vscode/*" \
  "v0-project/.idea/*" \
  "v0-project/node_modules/*" \
  "v0-project/venv/*" \
  ".venv/*" \
  "v0-project/dist/*" \
  "v0-project/*.pyc" \
  "v0-project/.DS_Store" \
  > /dev/null 2>&1

if [ $? -eq 0 ]; then
  SIZE=$(du -h "$ZIP_FILE" | cut -f1)
  echo "[v0] ✓ Zip file created successfully!"
  echo "[v0] Location: $ZIP_FILE"
  echo "[v0] Size: $SIZE"
  
  # Create latest symlink
  LATEST_LINK="$DIST_DIR/eni-apartments-latest.zip"
  rm -f "$LATEST_LINK"
  ln -s "eni-apartments-complete-$TIMESTAMP.zip" "$LATEST_LINK"
  echo "[v0] Latest link created: $LATEST_LINK"
else
  echo "[v0] Error creating zip file"
  exit 1
fi

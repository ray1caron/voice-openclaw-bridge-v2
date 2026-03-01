#!/bin/bash
# Create Production Deployment Bundle

set -e

echo "Creating Voice Bridge v2 v1.0.0-beta Deployment Bundle"

# Variables
DIST_DIR="dist"
BUNDLE_NAME="voice-bridge-v2-1.0.0-beta.tar.gz"
VERSION="1.0.0-beta"

# Create dist directory if it doesn't exist
mkdir -p "$DIST_DIR"

echo "Creating deployment bundle..."

# Create tarball with all necessary files
tar czf "$DIST_DIR/$BUNDLE_NAME" \
    src/ \
    config/ \
    scripts/ \
    tests/ \
    README.md \
    INSTALL.md \
    USER_GUIDE.md \
    BUG_TRACKER.md \
    CHANGELOG.md \
    RELEASENOTES.md \
    pyproject.toml \
    LICENSE \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.pytest_cache'

# Verify bundle was created
if [ -f "$DIST_DIR/$BUNDLE_NAME" ]; then
    SIZE=$(ls -lh "$DIST_DIR/$BUNDLE_NAME" | awk '{print $5}')
    echo "✓ Bundle created: $DIST_DIR/$BUNDLE_NAME ($SIZE)"
else
    echo "✗ Failed to create bundle"
    exit 1
fi

# Generate SHA256 checksum
echo "Generating SHA256 checksum..."
cd "$DIST_DIR"
sha256sum "$BUNDLE_NAME" > SHA256SUMS
cd ..
echo "✓ Checksums saved to $DIST_DIR/SHA256SUMS"

# Display checksum
echo ""
echo "SHA256 Checksum:"
cat "$DIST_DIR/SHA256SUMS"

echo ""
echo "Deployment bundle created successfully!"
echo "Location: $DIST_DIR/$BUNDLE_NAME"
echo "Checksum: $DIST_DIR/SHA256SUMS"
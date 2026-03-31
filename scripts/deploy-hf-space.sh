#!/usr/bin/env bash
# Deploy hf_space/ contents to a HuggingFace Space.
#
# Usage:
#   ./scripts/deploy-hf-space.sh                          # deploy to staging
#   ./scripts/deploy-hf-space.sh JammyMachina/the-jam-machine-app  # deploy to production
#
# Requires: huggingface-hub python package and valid HF login (huggingface-cli login)

set -euo pipefail

SPACE_ID="${1:-JammyMachina/the-jam-machine-staging}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
HF_SPACE_DIR="$REPO_ROOT/hf_space"
TMP_DIR=$(mktemp -d)

echo "Deploying to HuggingFace Space: $SPACE_ID"
echo "Source: $HF_SPACE_DIR"

# Clone the Space repo
echo "Cloning Space repo..."
git clone "https://huggingface.co/spaces/$SPACE_ID" "$TMP_DIR/space" 2>/dev/null || {
    echo "Error: Failed to clone Space. Make sure you're logged in (huggingface-cli login)."
    rm -rf "$TMP_DIR"
    exit 1
}

# Replace contents with hf_space/
echo "Copying files..."
cd "$TMP_DIR/space"
# Remove everything except .git
find . -maxdepth 1 -not -name '.git' -not -name '.gitattributes' -not -name '.' -delete 2>/dev/null || true
cp "$HF_SPACE_DIR"/* .

# Commit and push
git add -A
if git diff --cached --quiet; then
    echo "No changes to deploy."
else
    git commit -m "Deploy from $(git -C "$REPO_ROOT" rev-parse --short HEAD) ($(date -u +%Y-%m-%dT%H:%M:%SZ))"
    git push
    echo "Deployed successfully."
fi

# Cleanup
rm -rf "$TMP_DIR"
echo "Done. Space: https://huggingface.co/spaces/$SPACE_ID"

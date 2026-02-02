#!/bin/bash
set -e

echo "=========================================="
echo "Setting up The Jam Machine development environment"
echo "=========================================="

# Check for Python 3.11+
python_version=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+')
major=$(echo "$python_version" | cut -d. -f1)
minor=$(echo "$python_version" | cut -d. -f2)

if [ "$major" -lt 3 ] || { [ "$major" -eq 3 ] && [ "$minor" -lt 11 ]; }; then
    echo "Error: Python 3.11 or higher is required (found $python_version)"
    exit 1
fi
echo "✓ Python $python_version detected"

# Check for FluidSynth
if ! command -v fluidsynth &> /dev/null; then
    echo "Warning: FluidSynth not found. Audio playback will not work."
    echo "Install with:"
    echo "  macOS: brew install fluidsynth"
    echo "  Linux: sudo apt install fluidsynth"
else
    echo "✓ FluidSynth detected"
fi

# Install pipenv if not present
if ! command -v pipenv &> /dev/null; then
    echo "Installing pipenv..."
    pip install pipenv
fi
echo "✓ pipenv available"

# Install dependencies
echo ""
echo "Installing project dependencies..."
pipenv install -e ".[ci]"

# Install additional dev tools
echo ""
echo "Installing additional dev tools..."
pipenv run pip install pip-audit

# Set up git hooks
echo ""
echo "Setting up git hooks..."
git config core.hooksPath .githooks
chmod +x .githooks/*
echo "✓ Git hooks configured"

# Verify installation
echo ""
echo "Verifying installation..."
pipenv run python -c "import the_jam_machine; print('✓ the_jam_machine package importable')"
pipenv run ruff --version > /dev/null && echo "✓ ruff available"
pipenv run pytest --version > /dev/null && echo "✓ pytest available"

echo ""
echo "=========================================="
echo "Environment setup complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Run 'pipenv shell' to activate the environment"
echo "  2. Run 'pipenv run pytest test/' to run tests"
echo "  3. Run 'pipenv run ruff check src/ test/' to lint code"
echo ""

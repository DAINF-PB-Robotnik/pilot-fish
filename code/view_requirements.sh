#!/usr/bin/env bash
# This script generates requirements.txt by listing all installed packages
# in the current Python environment. If a .venv directory exists, it will
# be automatically activated before freezing.

set -euo pipefail

# 1) If a virtual environment named .venv exists, activate it
if [ -d ".venv" ]; then
    # shellcheck disable=SC1091
    source .venv/bin/activate
    echo "Activated virtual environment .venv/"
fi

# 2) Inform user and dump installed packages to requirements.txt
echo "Generating requirements.txt using pip freeze..."
pip freeze > requirements.txt

# 3) Notify completion
echo "✅ requirements.txt created with the following packages:"
cat requirements.txt

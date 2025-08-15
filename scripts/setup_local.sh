#!/usr/bin/env bash
set -euo pipefail

py="${PYTHON:-python3}"
$py -m venv .venv
# shellcheck disable=SC1091
if [ -f ".venv/bin/activate" ]; then
  source .venv/bin/activate
else
  source .venv/Scripts/activate
fi

pip install --upgrade pip
pip install -r requirements.txt

# Linux heads-up for Tk GUI
if command -v apt >/dev/null 2>&1; then
  python3 - <<'PY' >/dev/null 2>&1 || {
import tkinter
PY
    echo "[info] tkinter not detected. If GUI fails, run: sudo apt install -y python3-tk"
  }
fi

echo "✅ Setup complete."
echo "Next steps:"
echo "  1) Edit .env (replace __REPLACE_ME__ placeholders)."
echo "  2) Run: bash scripts/smoke_test.sh"
echo "  3) Run: payroll --dry-run (optional explicit CSV: examples/payroll_mock.csv)"
echo "  4) Run: payroll"

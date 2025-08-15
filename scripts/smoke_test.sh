#!/usr/bin/env bash
set -euo pipefail

if [ ! -f .env ]; then
  echo "❌ No .env found. Copy template and fill placeholders."
  exit 1
fi

req=(HOST USER REMOTE_DIR LIB PROGRAM USE_SSH)
missing=0
for k in "${req[@]}"; do
  if ! grep -q "^$k=" .env; then
    echo "❌ Missing $k in .env"
    missing=1
  fi
done
[ "$missing" -eq 0 ] || exit 1

echo "[*] Running dry-run with mock CSV if present..."
if [ -f examples/payroll_mock.csv ]; then
  payroll --dry-run examples/payroll_mock.csv
else
  payroll --dry-run
fi
echo "✅ Dry-run passed"

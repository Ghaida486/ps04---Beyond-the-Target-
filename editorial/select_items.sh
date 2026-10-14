#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
exec python3 editorial/select_items.py "$@"

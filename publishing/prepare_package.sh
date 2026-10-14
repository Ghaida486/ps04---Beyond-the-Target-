#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
exec python3 publishing/prepare_package.py "$@"

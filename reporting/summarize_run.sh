#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
exec python3 reporting/summarize_run.py "$@"

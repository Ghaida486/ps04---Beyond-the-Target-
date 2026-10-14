#!/usr/bin/env bash
set -uo pipefail
cd "$(dirname "$0")"
source lib/workflow.sh
started=$(date -u +%Y-%m-%dT%H:%M:%SZ)
if [[ $# == 2 && $1 == --package ]]; then
  run=$2
  [[ -f "$run/run.json" ]] || { echo 'Unknown run directory' >&2; exit 2; }
  status=0
  bash review/check_content.sh "$run" > "$run/review.json" || status=1
  if [[ $status == 0 ]]; then bash publishing/prepare_package.sh "$run" > "$run/package-result.json" || status=1; fi
elif [[ $# == 0 ]]; then
  run=$(python3 lib/new_run.py) || exit "$?"
  status=0
  bash data/store.sh init || status=1
  bash workflows/collect_sources.sh "$run" || status=1
  bash workflows/create_series.sh "$run" || status=1
else
  echo 'Usage: bash run.sh [--package runs/RUN_ID]' >&2
  exit 2
fi
workflow_receipt "$run" run "$status" "$started"
bash reporting/summarize_run.sh "$run" > "$run/summary.json" || exit 1
cat "$run/summary.json"
python3 - "$run/summary.json" <<'PY'
import json,sys
sys.exit(1 if json.load(open(sys.argv[1]))['status']=='failed' else 0)
PY

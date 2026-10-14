#!/usr/bin/env bash
set -uo pipefail
cd "$(dirname "$0")/.."
source lib/workflow.sh
[[ $# == 1 ]] || exit 2
run=$1
started=$(date -u +%Y-%m-%dT%H:%M:%SZ)
status=0
bash editorial/select_items.sh "$run" < "$run/eligible.jsonl" > "$run/decisions.jsonl" || status=1
if [[ $status == 0 ]]; then
  bash editorial/create_briefs.sh "$run" < "$run/decisions.jsonl" > "$run/briefs.jsonl" || status=1
fi
if [[ $status == 0 ]]; then
  bash content/write_articles.sh "$run" < "$run/briefs.jsonl" > "$run/articles.jsonl" || status=1
  bash content/write_video_scripts.sh "$run" < "$run/briefs.jsonl" > "$run/video_scripts.jsonl" || status=1
fi
bash review/check_content.sh "$run" > "$run/review.json" || status=1
workflow_receipt "$run" create_series "$status" "$started"
exit "$status"

#!/usr/bin/env bash
set -uo pipefail
cd "$(dirname "$0")/.."
source lib/workflow.sh
[[ $# == 1 ]] || exit 2
run=$1
started=$(date -u +%Y-%m-%dT%H:%M:%SZ)
mkdir -p "$run/candidates"
status=0
bash collectors/fetch_feeds.sh "$run" > "$run/candidates/feeds.jsonl" || status=1
bash collectors/fetch_youtube.sh "$run" > "$run/candidates/youtube.jsonl" || status=1
bash collectors/fetch_podcasts.sh "$run" > "$run/candidates/podcasts.jsonl" || status=1
cat "$run/candidates/feeds.jsonl" "$run/candidates/youtube.jsonl" "$run/candidates/podcasts.jsonl" > "$run/candidates.jsonl"
cat "$run/candidates.jsonl" | bash processing/extract_content.sh "$run" > "$run/items.jsonl" || status=1
bash data/store.sh upsert "$run" < "$run/items.jsonl" > "$run/changes.jsonl" || status=1
bash data/store.sh list > "$run/corpus.jsonl" || status=1
bash processing/filter_items.sh "$run" < "$run/corpus.jsonl" > "$run/eligible.jsonl" || status=1
workflow_receipt "$run" collect_sources "$status" "$started"
exit "$status"

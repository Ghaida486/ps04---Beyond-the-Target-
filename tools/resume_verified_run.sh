#!/usr/bin/env bash
# Resume a held run after extraction, preserving the pre-verification artifacts.
set -uo pipefail
cd "$(dirname "$0")/.."
[[ $# == 1 && -f "$1/run.json" && -f "$1/maintenance.json" ]] || exit 2
run=$1
while [[ ! -f "$run/summary.json" ]]; do sleep 5; done
backup="$run/before-date-verification"
[[ ! -e "$backup" ]] || { echo 'A verification backup already exists; inspect before retrying.' >&2; exit 2; }
mkdir -p "$backup"
for name in items.jsonl changes.jsonl corpus.jsonl eligible.jsonl exclusions.jsonl decisions.jsonl review.json summary.json; do
  [[ ! -f "$run/$name" ]] || cp "$run/$name" "$backup/$name"
done
status=0
bash processing/extract_content.sh "$run" < "$run/candidates.jsonl" > "$run/items.verified.jsonl" || status=1
mv "$run/items.verified.jsonl" "$run/items.jsonl"
bash data/store.sh upsert "$run" < "$run/items.jsonl" > "$run/changes.jsonl" || exit 1
bash data/store.sh list > "$run/corpus.jsonl" || exit 1
bash processing/filter_items.sh "$run" < "$run/corpus.jsonl" > "$run/eligible.jsonl" || exit 1
python3 - "$run" <<'PY'
import sys
sys.path.insert(0,'lib')
from common import *
r=Path(sys.argv[1]);before={x['item_id']:x for x in rows(r/'before-date-verification/items.jsonl')};changes=[]
for item in rows(r/'items.jsonl'):
 old=before.get(item['item_id'])
 if old and any(old.get(k)!=item.get(k) for k in ('published_at','title','url')):
  changes.append({'item_id':item['item_id'],'old_version_id':old['version_id'],'new_version_id':item['version_id'],'before':{k:old.get(k) for k in ('published_at','title','url')},'after':{k:item.get(k) for k in ('published_at','title','url')},'reason':'Assistant verification against originating article metadata/visible calendar date and canonical title/URL; not student sign-off.'})
write(r/'date_verification.json',changes)
PY
rm "$run/maintenance.json"
bash workflows/create_series.sh "$run" || status=1
bash reporting/summarize_run.sh "$run" > "$run/summary.json" || exit 1
python3 tools/catalogue_sources.py "$run" > "$run/catalogue-result.json"
if [[ -s "$run/decisions.jsonl" ]]; then python3 tools/prepare_review.py "$run" > "$run/student-review-result.json"; fi
cat "$run/summary.json"
exit "$status"

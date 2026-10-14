"""Catalogue actual discoveries and extraction status; does not mark editorial acceptance."""
import sys
sys.path.insert(0,'lib')
from common import *

def main():
    if len(sys.argv)!=2:return 2
    run=Path(sys.argv[1]);candidates=rows(run/'candidates.jsonl');items=rows(run/'items.jsonl') if (run/'items.jsonl').exists() else []
    latest={x['item_id']:x for x in items}; catalogue=[]
    current_ids={x['item_id'] for x in candidates}
    if (run/'eligible.jsonl').exists():
        for retained in rows(run/'eligible.jsonl'):
            latest.setdefault(retained['item_id'],retained)
            if retained['item_id'] not in current_ids:candidates.append(retained)
    asof=dt.date.fromisoformat(read(run/'run.json')['as_of_date'])
    for c in candidates:
        item=latest.get(c['item_id']); data=item or c
        if eligible_reason(data['published_at'],asof):continue
        catalogue.append({'item_id':data['item_id'],'title':data['title'],'publisher_id':data['publisher_id'],'kind':data['kind'],'published_at':data['published_at'],'url':data['url'],'discovered_this_run':data['item_id'] in current_ids,'extracted':item is not None,'text_path':item['text_path'] if item else None,'segments_path':item['segments_path'] if item else None,'editorial_status':'not established by this catalogue'})
    catalogue=list({x['item_id']:x for x in catalogue}.values())
    write(run/'source_catalogue.json',{'as_of_date':str(asof),'window_start':str(asof-dt.timedelta(days=29)),'status':'discovery/extraction catalogue; not an editorial approval','items':catalogue})
    lines=['# Source catalogue — Beyond the Target',f'Actual run: `{run}`. Window: {asof-dt.timedelta(days=29)} through {asof}. Discovery alone is not accepted evidence.','| Source item | Producer | Type | Published | Extracted |','| --- | --- | --- | --- | --- |']
    for x in catalogue:lines.append(f'| [{x["title"].replace("|","/")}]({x["url"]}) | {x["publisher_id"]} | {x["kind"]} | {x["published_at"][:10]} | {"yes" if x["extracted"] else "pending"} |')
    (run/'source_catalogue.md').write_text('\n\n'.join(lines[:3])+'\n'+'\n'.join(lines[3:])+'\n')
    emit({'catalogue':str(run/'source_catalogue.md'),'distinct_recent_candidates':len(catalogue),'extracted_recent_items':sum(x['extracted'] for x in catalogue),'publishers':sorted({x['publisher_id'] for x in catalogue})});return 0
invoke(main)

import sys
sys.path.insert(0,'lib')
from common import *
from collections import Counter

def main():
    if len(sys.argv)!=2: return 2
    run=Path(sys.argv[1]); stage=Stage(run,'summarize_run'); meta=read(run/'run.json')
    def optional(name): return rows(run/name) if (run/name).is_file() else None
    candidates=optional('candidates.jsonl'); items=optional('items.jsonl'); changes=optional('changes.jsonl'); eligible=optional('eligible.jsonl'); excluded=optional('exclusions.jsonl'); decisions=optional('decisions.jsonl'); articles=optional('articles.jsonl'); videos=optional('video_scripts.jsonl')
    receipts=[read(p) for p in (run/'logs').glob('*.json')]; latest={}
    for r in sorted(receipts,key=lambda x:x['started_at']): latest[r['stage']]=r
    failed=[x['stage'] for x in latest.values() if x['status']!='success' and x['stage']!='summarize_run']
    review=read(run/'review.json') if (run/'review.json').is_file() else None
    package=read(run/'package/manifest.json') if (run/'package/manifest.json').is_file() else None
    approval=read(run/'approval.json') if (run/'approval.json').is_file() else None
    ready=bool(package and review and review['passed'] and approval and approval.get('decision')=='approve' and approval.get('review_id')==review['review_id']==package['review_id'])
    status='ready_for_production' if ready else ('awaiting_review' if review and review['passed'] else 'failed')
    counts={}
    for key,values in [('discovered',candidates),('extracted',items),('eligible',eligible),('excluded',excluded),('articles',articles),('video_scripts',videos)]: counts[key]=len(values) if values is not None else None
    for change in ('new','changed','unchanged'): counts[change]=sum(x['change']==change for x in changes) if changes is not None else None
    for decision,label in [('accept','accepted'),('reject','rejected'),('defer','deferred')]: counts[label]=sum(x['decision']==decision for x in decisions) if decisions is not None else None
    distinct={x.get('underlying_id',x['item_id']):x for x in (eligible or [])}
    unknown=[r['stage'] for r in receipts if r['cost_usd'] is None]
    result={'run_id':meta['run_id'],'status':status,'counts':counts,'coverage':{'distinct_eligible_items':len(distinct) if eligible is not None else None,'by_kind':dict(Counter(x['kind'] for x in distinct.values())),'independent_publishers':sorted({x['publisher_id'] for x in distinct.values()})},'duplicate_observations':len(candidates)-len({x.get('underlying_id',x['item_id']) for x in candidates}) if candidates is not None else None,'failed_or_incomplete_stages':failed,'elapsed_seconds':(dt.datetime.fromisoformat(now().replace('Z','+00:00'))-dt.datetime.fromisoformat(meta['started_at'].replace('Z','+00:00'))).total_seconds(),'tools':sorted({t for r in receipts for t in r['tools']}),'known_or_estimated_cost_usd':sum(r['cost_usd'] for r in receipts if r['cost_usd'] is not None),'unknown_cost_stages':unknown,'remaining_manual_actions':['Student reviews three accepted and three rejected/deferred decisions; revises policy and reruns affected stages.','Student reviews evidence and drafts, corrects claims, and supplies approval.json.','Complete two live runs on different UTC days within assignment week.','Produce videos in Google Vids or HeyGen; publish and cross-link Substack/YouTube; record technical demo.'],'publication_links':read(run/'package/publication_links.json') if (run/'package/publication_links.json').exists() else None}
    emit(result); stage.output=1; return stage.finish()
invoke(main)

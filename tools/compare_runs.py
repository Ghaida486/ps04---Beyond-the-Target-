"""Compare retained evidence and editorial decisions without rerunning either run."""
import sys
sys.path.insert(0,'lib')
from common import *

def main():
    if len(sys.argv)!=3:return 2
    left,right=map(Path,sys.argv[1:]); a=read(left/'run.json');b=read(right/'run.json')
    def load(run,file,key):
        return {tuple(x[k] for k in key):x for x in rows(run/file)} if (run/file).exists() else None
    old=load(left,'items.jsonl',['item_id']);new=load(right,'items.jsonl',['item_id'])
    decisions_a=load(left,'decisions.jsonl',['item_id']);decisions_b=load(right,'decisions.jsonl',['item_id'])
    result={'left_run':a['run_id'],'right_run':b['run_id'],'dates':[a['as_of_date'],b['as_of_date']],'different_days':a['as_of_date']!=b['as_of_date'],'note':'Same-day retries do not satisfy the different-day live-run requirement. Extraction recovery is not newly published source material.','new_items':None,'changed_versions':None,'unchanged_versions':None,'editorial_changes':None}
    if old is not None and new is not None:
        result['new_items']=[k[0] for k in new if k not in old]
        result['changed_versions']=[k[0] for k in new if k in old and new[k]['version_id']!=old[k]['version_id']]
        result['unchanged_versions']=[k[0] for k in new if k in old and new[k]['version_id']==old[k]['version_id']]
    if decisions_a is not None and decisions_b is not None:
        result['editorial_changes']=[{'item_id':k[0],'before':decisions_a.get(k),'after':v} for k,v in decisions_b.items() if v!=decisions_a.get(k)]
    source_a=load(left,'candidates.jsonl',['item_id']);source_b=load(right,'candidates.jsonl',['item_id'])
    result['newly_discovered_source_ids']=[k[0] for k in source_b if k not in source_a] if source_a is not None and source_b is not None else None
    write(right/'comparison.json',result);emit(result);return 0
invoke(main)

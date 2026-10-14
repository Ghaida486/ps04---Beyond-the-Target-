import sys
sys.path.insert(0,'lib')
from common import *
def main():
    if len(sys.argv)!=2: return 2
    run=Path(sys.argv[1]); stage=Stage(run,'filter_items'); values=rows(); stage.input=len(values)
    asof=dt.date.fromisoformat(read(run/'run.json')['as_of_date']); excluded=[]
    for item in values:
        reason=eligible_reason(item['published_at'],asof)
        if reason: excluded.append({'item_id':item['item_id'],'version_id':item['version_id'],'reason':reason,'detail':f'Publication {item["published_at"]}; inclusive UTC window {asof-dt.timedelta(days=29)} through {asof}.'})
        else: emit(item); stage.output+=1
    jsonl(run/'exclusions.jsonl',excluded); return stage.finish()
invoke(main)

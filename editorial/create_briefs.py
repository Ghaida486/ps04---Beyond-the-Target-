import sys
sys.path.insert(0,'lib')
from common import *
def main():
    if len(sys.argv)!=2: return 2
    run=Path(sys.argv[1]); stage=Stage(run,'create_briefs')
    try:
        decisions=rows(); stage.input=len(decisions); eligible=rows(run/'eligible.jsonl'); accepted={(d['item_id'],d['version_id']) for d in decisions if d['decision']=='accept'}
        items=[x for x in eligible if (x['item_id'],x['version_id']) in accepted]
        unique={x.get('underlying_id',x['item_id']):x for x in eligible}
        if len(unique)<12 or len({x['publisher_id'] for x in unique.values()})<6: raise RuntimeError('Evidence gate: need 12 collected eligible distinct items from six independent publishers')
        if any(sum(x['kind']==kind for x in unique.values())<2 for kind in ('feed','youtube','podcast')): raise RuntimeError('Evidence gate: need two collected eligible substantive items of each input kind')
        briefs=model(run,stage,'create_briefs',{'project':read(run/'config/project.json'),'as_of_date':read(run/'run.json')['as_of_date'],'decisions':decisions,'items':evidence(items)})['briefs']
        if sorted(x['piece_id'] for x in briefs)!=['01','02','03']: raise ValueError('Exactly three piece IDs required')
        for b in briefs:
            for key in ('title','question','argument','synthesis','limitations','claims'):
                if not b.get(key): raise ValueError(f'Brief missing {key}')
            publishers=set()
            for c in b['claims']:
                if c['type'] not in ('reported_fact','source_claim','inference') or not c['evidence']: raise ValueError('Every claim requires valid type and evidence')
                for ref in c['evidence']:
                    if (ref['item_id'],ref['version_id']) not in accepted: raise ValueError('Brief cites unaccepted evidence')
                    publishers.add(next(x['publisher_id'] for x in items if x['item_id']==ref['item_id'] and x['version_id']==ref['version_id']))
            if len(publishers)<3: raise ValueError('Each piece needs three independent publishers')
        for b in briefs: emit(b); stage.output+=1
        return stage.finish()
    except Exception as e: stage.error(e); return stage.finish(1)
invoke(main)

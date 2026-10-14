import sys
sys.path.insert(0,'lib')
from common import *
def main():
    if len(sys.argv)!=2: return 2
    run=Path(sys.argv[1]); stage=Stage(run,'select_items')
    try:
        items=rows(); stage.input=len(items)
        if (run/'maintenance.json').exists(): raise RuntimeError('Editorial stage held for original publication-date verification; resume after maintenance is cleared')
        if not items: raise RuntimeError('No eligible evidence available for editorial selection')
        result=model(run,stage,'select_items',{'project':read(run/'config/project.json'),'items':evidence(items),'source_verification':read(run/'config/source_verification.json') if (run/'config/source_verification.json').exists() else None})['decisions']
        publishers={(x['item_id'],x['version_id']):x['publisher_id'] for x in items}
        support={piece:{publishers.get((d.get('item_id'),d.get('version_id'))) for d in result if d.get('decision')=='accept' and piece in d.get('piece_ids',[])}-{None} for piece in ('01','02','03')}
        shortfall={piece:len(producers) for piece,producers in support.items() if len(producers)<3}
        if shortfall:
            jsonl(run/'editorial_revisions'/('initial-assignments-'+uuid.uuid4().hex+'.jsonl'),result)
            result=model(run,stage,'select_items',{'project':read(run/'config/project.json'),'items':evidence(items),'source_verification':read(run/'config/source_verification.json') if (run/'config/source_verification.json').exists() else None,'previous_decisions':result,'assignment_feedback':{'independent_publisher_shortfalls':shortfall,'instruction':'Review justified intended-piece assignments, including original current-event reports with audience context. Do not accept weak items, invent sources or claim independent corroboration from repetitions. If evidence does not support a repair, keep the limitation explicit.'}})['decisions']
        expected={(x['item_id'],x['version_id']) for x in items}; seen=set()
        for d in result:
            key=(d['item_id'],d['version_id'])
            if key not in expected or key in seen: raise ValueError('Missing, duplicate or unknown decision reference')
            if d['decision'] not in ('accept','reject','defer') or not d['reason'].strip(): raise ValueError('Invalid editorial decision')
            if not isinstance(d['piece_ids'],list) or any(x not in ('01','02','03') for x in d['piece_ids']): raise ValueError('Invalid intended pieces')
            if (d['decision']=='accept') != bool(d['piece_ids']): raise ValueError('Accepted items need pieces; rejected/deferred items must have none')
            seen.add(key)
        if seen!=expected: raise ValueError('AI omitted candidate decisions')
        for d in result: emit(d); stage.output+=1
        return stage.finish()
    except Exception as e: stage.error(e); return stage.finish(1)
invoke(main)

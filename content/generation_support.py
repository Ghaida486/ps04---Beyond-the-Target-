"""Rendering support shared by the two content generators."""
import sys
sys.path.insert(0,'lib')
from common import *

def generate(run,kind):
    stage=Stage(run,'write_'+kind)
    try:
        briefs=rows(); stage.input=len(briefs); items=rows(Path(run)/'eligible.jsonl')
        for brief in briefs:
            ids={(r['item_id'],r['version_id']) for c in brief['claims'] for r in c['evidence']}
            material=[x for x in items if (x['item_id'],x['version_id']) in ids]
            context=evidence(material)
            for source in context:
                if source['segments'] is None: continue
                cited={ref['locator'].get('segment_id') for claim in brief['claims'] for ref in claim['evidence'] if ref['item_id']==source['item_id'] and ref['version_id']==source['version_id'] and ref['locator']['type']=='segment'}
                segments=source['segments'];positions={i for i,segment in enumerate(segments) if segment['segment_id'] in cited}
                nearby={j for i in positions for j in (i-1,i,i+1) if 0<=j<len(segments)}
                source['segments']=[segment for i,segment in enumerate(segments) if i in nearby]
                source['context_scope']='Referenced segments with adjacent context; complete original transcript remains at segments_path.'
            result=model(run,stage,'write_'+kind,{'project':read(Path(run)/'config/project.json'),'as_of_date':read(Path(run)/'run.json')['as_of_date'],'brief':brief,'items':context})
            markdown=result['markdown']; claim_ids=[c['claim_id'] for c in brief['claims']]
            if not all(c in markdown for c in claim_ids): raise ValueError('Generated content omitted claim markers')
            path=Path(run)/kind/(brief['piece_id']+'.md'); path.parent.mkdir(parents=True,exist_ok=True); path.write_text(markdown+'\n')
            emit({'piece_id':brief['piece_id'],'path':str(path),'claim_ids':claim_ids}); stage.output+=1
        return stage.finish()
    except Exception as e: stage.error(e); return stage.finish(1)

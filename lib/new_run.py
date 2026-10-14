from common import *
import shutil

def main():
    p=read('config/project.json'); sources=read('config/sources.json')
    if any(not isinstance(p.get(k),str) or not p[k].strip() for k in ('publication_name','topic','audience','central_question')): raise ValueError('Project brief incomplete')
    if not isinstance(sources,list) or not sources: raise ValueError('Configure sources before running')
    for s in sources:
        if any(not isinstance(s.get(k),str) or not s[k].strip() for k in ('source_id','publisher_id','kind','url')) or s['kind'] not in ('feed','youtube','podcast'): raise ValueError('Invalid source configuration')
    for kind in ('feed','youtube','podcast'):
        if not any(s['kind']==kind for s in sources): raise ValueError('Missing source kind: '+kind)
    previous=sorted(Path('runs').glob('*/run.json')) if Path('runs').exists() else []
    stamp=now(); run_id=dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:6]; run=Path('runs')/run_id; run.mkdir(parents=True)
    shutil.copytree('config',run/'config'); shutil.copytree('prompts',run/'prompts')
    write(run/'run.json',{'run_id':run_id,'started_at':stamp,'as_of_date':stamp[:10],'mode':'live','previous_run_id':read(previous[-1])['run_id'] if previous else None})
    print(run); return 0
invoke(main)

import sys
sys.path[:0]=['lib','review']
from common import *
from check_content import assess
import shutil

def main():
    if len(sys.argv)!=2: return 2
    run=Path(sys.argv[1]); stage=Stage(run,'prepare_package')
    try:
        current=assess(run); approval=read(run/'approval.json')
        if not current['passed']: raise RuntimeError('Content checks have blocking issues')
        if approval.get('review_id')!=current['review_id'] or approval.get('decision')!='approve': raise RuntimeError('Student approval missing, stale or requests revision')
        if any(not approval.get(k) for k in ('reviewer','reviewed_at','notes')): raise RuntimeError('Student approval requires reviewer, reviewed_at and notes')
        package=run/'package'; package.mkdir(exist_ok=True); assets=[]
        items={(x['item_id'],x['version_id']):x for x in rows(run/'eligible.jsonl')}
        for brief in rows(run/'briefs.jsonl'):
            pid=brief['piece_id']
            for kind in ('articles','video_scripts'):
                original=next(x for x in rows(run/(kind+'.jsonl')) if x['piece_id']==pid); dest=package/kind/(pid+'.md'); dest.parent.mkdir(exist_ok=True); shutil.copyfile(original['path'],dest)
                assets.append({'piece_id':pid,'kind':kind,'path':str(dest)})
            notes=[]
            for claim in brief['claims']:
                notes.append('## '+claim['claim_id']+'\n'+claim['statement'])
                for ref in claim['evidence']:
                    item=items[(ref['item_id'],ref['version_id'])]; loc=ref['locator']; link=item['url']
                    if loc['type']=='segment':
                        seg=next(s for s in read(item['segments_path']) if s['segment_id']==loc['segment_id']); seconds=int(seg['start_seconds']); link+=('&' if '?' in link else '?')+'t='+str(seconds); passage=f'{seg["start_seconds"]:.1f}–{seg["end_seconds"]:.1f}s: '+seg['text']
                    else: passage=loc['quote']
                    notes.append(f'- [{item["title"]}]({link}) — {passage}\n  Source version: {item["version_id"]}')
            path=package/(pid+'-source-notes.md'); path.write_text('\n\n'.join(notes)+'\n'); assets.append({'piece_id':pid,'kind':'source_notes','path':str(path)})
        links=package/'publication_links.json'
        if not links.exists(): write(links,[{'piece_id':pid,'substack_url':None,'youtube_url':None} for pid in ('01','02','03')])
        actions=['Produce each 3–5 minute video in Google Vids or HeyGen; inspect pronunciation, attribution and evidence links.','Publish three free-access Substack articles and three public/unlisted YouTube videos; cross-link each pair.','Fill real publication URLs and verify course-staff access.','Record a separate 4–6 minute narrated technical demonstration.']
        manifest={'review_id':current['review_id'],'assets':assets,'manual_steps':actions,'publication_links_path':str(links),'published':False}
        write(package/'manifest.json',manifest); emit(manifest); stage.output=len(assets); return stage.finish()
    except Exception as e: stage.error(e); return stage.finish(1)
invoke(main)

import sys
sys.path.insert(0,'lib')
from common import *
import re

def narration_words(text):
    blocks=re.findall(r"\*\*NARRATION:?\*\*\s*:?\s*(.*?)(?=\n\*\*VISUAL:?\*\*|\n## |\Z)",text,re.S)
    return re.sub(r"<!--.*?-->","", "\n".join(blocks),flags=re.S) if blocks else None

def assess(run):
    run=Path(run); issues=[]; inputs={'checker_implementation':digest(Path(__file__).read_text())}; used={}; media=set(); used_items={}; narration_counts={}
    def issue(artifact,message,severity='error'): issues.append({'artifact':artifact,'severity':severity,'explanation':message})
    def capture(p):
        p=Path(p)
        if not p.is_file(): issue(str(p),'Required artifact missing'); inputs[str(p)]=None; return None
        inputs[str(p)]=p.read_bytes().hex(); return p
    required=['run.json','briefs.jsonl','eligible.jsonl','decisions.jsonl','articles.jsonl','video_scripts.jsonl']
    for name in required: capture(run/name)
    if any(inputs[str(run/n)] is None for n in required): return {'review_id':digest(inputs),'passed':False,'issues':issues}
    asof=read(run/'run.json')['as_of_date']; briefs=rows(run/'briefs.jsonl'); items={(x['item_id'],x['version_id']):x for x in rows(run/'eligible.jsonl')}
    accepted={(d['item_id'],d['version_id']):d for d in rows(run/'decisions.jsonl') if d['decision']=='accept'}
    if sorted(b['piece_id'] for b in briefs)!=['01','02','03']: issue('briefs','Three distinct piece IDs required')
    if len({b.get('argument','').strip().lower() for b in briefs})!=3: issue('briefs','Central arguments must differ')
    for b in briefs:
        piece=b['piece_id']; publishers=set(); claim_ids=set()
        for field in ('title','question','argument','synthesis','limitations'):
            if not b.get(field): issue(piece,'Missing brief '+field)
        for claim in b['claims']:
            cid=claim['claim_id']
            if cid in claim_ids or not cid.startswith(piece+'-c'): issue(piece,'Invalid or duplicate claim marker')
            claim_ids.add(cid)
            if not claim.get('statement') or claim.get('type') not in ('reported_fact','source_claim','inference'): issue(piece,'Invalid claim statement/type')
            if not claim.get('evidence'): issue(piece,'Claim lacks evidence: '+cid)
            for ref in claim.get('evidence',[]):
                key=(ref['item_id'],ref['version_id']); item=items.get(key)
                if item is None: issue(piece,'Unresolvable evidence version'); continue
                if key not in accepted or piece not in accepted[key]['piece_ids']: issue(piece,'Evidence not accepted for this piece')
                publishers.add(item['publisher_id']); used_items[item.get('underlying_id',item['item_id'])]=item; media.add(item['kind']); used[key]=item
                reason=eligible_reason(item.get('published_at'),dt.date.fromisoformat(asof))
                if reason: issue(piece,'Ineligible evidence: '+reason)
                textpath=capture(item['text_path']); segpath=capture(item['segments_path']) if item['segments_path'] else None
                locator=ref['locator']
                if item['kind']=='feed':
                    quote=locator.get('quote','')
                    if locator.get('type')!='text' or not quote or textpath is None or quote not in textpath.read_text(): issue(piece,'Written quote does not resolve exactly')
                else:
                    segments=read(segpath) if segpath else []
                    if locator.get('type')!='segment' or not any(s['segment_id']==locator.get('segment_id') for s in segments): issue(piece,'Media timestamp segment does not resolve')
                    if any(not isinstance(s.get('start_seconds'),(int,float)) or s['end_seconds']<s['start_seconds'] or not s.get('text') for s in segments): issue(piece,'Invalid transcript segment')
        if len(publishers)<3: issue(piece,'Fewer than three independent supporting publishers')
        for kind in ('articles','video_scripts'):
            records=[x for x in rows(run/(kind+'.jsonl')) if x['piece_id']==piece]
            if len(records)!=1: issue(piece,'Expected one '+kind+' manifest'); continue
            m=records[0]; path=capture(m['path'])
            if set(m['claim_ids'])!=claim_ids: issue(piece,kind+' manifest claim mismatch')
            if path:
                text=path.read_text()
                if asof not in text: issue(piece,kind+' missing actual as-of date')
                for cid in claim_ids:
                    if cid not in text: issue(piece,kind+' missing claim marker '+cid)
                body=re.split(r'\n#{1,3}\s+(?:References|Sources|Source notes)',text,flags=re.I)[0]
                if kind=='video_scripts':
                    spoken=narration_words(body)
                    if spoken is None: issue(piece,'Narration labels not recognized; verify spoken duration manually','warning')
                    else: body=spoken
                words=len(re.findall(r"\b[\w’'-]+\b",body))
                if kind=='video_scripts': narration_counts[piece]=words
                lo,hi=(600,900) if kind=='articles' else (390,750)
                if not lo<=words<=hi: issue(piece,f'{kind}: {words} words; inspect target length and narration timing','warning')
                if 'http' not in text: issue(piece,kind+' lacks audience-facing source links')
        issue(piece,'Student must verify argument quality, limitations, factual support, narration timing, and article/script semantic consistency. Claim-marker agreement alone is insufficient.','warning')
    collected={x.get('underlying_id',x['item_id']):x for x in items.values()}
    if len(collected)<12: issue('series','Fewer than 12 collected distinct eligible items')
    if len({x['publisher_id'] for x in collected.values()})<6: issue('series','Fewer than six independent collected publishers')
    if media!={'feed','youtube','podcast'}: issue('series','All three input types must contribute cited evidence')
    for kind in ('feed','youtube','podcast'):
        if sum(x['kind']==kind for x in collected.values())<2: issue('series','Fewer than two collected eligible items of type '+kind)
    for kind in ('articles','video_scripts'):
        if sorted(m['piece_id'] for m in rows(run/(kind+'.jsonl')))!=['01','02','03']: issue(kind,'Manifest must contain exactly three pieces')
    return {'review_id':digest(inputs),'passed':not any(i['severity']=='error' for i in issues),'issues':issues,'as_of_date':asof,'narration_word_counts':narration_counts,'approx_minutes_at_130_words_per_minute':{p:round(n/130,2) for p,n in narration_counts.items()}}

def main():
    if len(sys.argv)!=2: return 2
    stage=Stage(sys.argv[1],'check_content')
    try: result=assess(sys.argv[1]); stage.input=6; emit(result); stage.output=1; return stage.finish()
    except Exception as e: stage.error(e); return stage.finish(1)
if __name__=='__main__': invoke(main)

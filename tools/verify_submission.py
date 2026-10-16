#!/usr/bin/env python3
"""Offline inspection of the committed submission, plus an isolated real-stage replay.

No model calls, downloads, production writes or direct database reads. The replay
uses the actual store/filter commands in a temporary copy of their owning code.
"""
import argparse, collections, datetime, hashlib, json, os, re, shutil, subprocess, sys, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RUNS=['20261014T175929Z-d79199','20261015T161701Z-ddbccc']
def read(p):return json.loads(p.read_text())
def rows(p):return [json.loads(x) for x in p.read_text().splitlines() if x.strip()]
def require(ok,message):
 if not ok:raise AssertionError(message)
def run_stage(root,args,input_text=None):
 r=subprocess.run(['bash',*args],cwd=root,input=input_text,text=True,capture_output=True)
 require(r.returncode==0,f'{args}: exit {r.returncode}: {r.stderr}')
 return [json.loads(x) for x in r.stdout.splitlines() if x.strip()]
def inspect():
 os.chdir(ROOT)
 expected=['run.sh','workflows/collect_sources.sh','workflows/create_series.sh','collectors/fetch_feeds.sh','collectors/fetch_youtube.sh','collectors/fetch_podcasts.sh','processing/extract_content.sh','processing/filter_items.sh','data/store.sh','editorial/select_items.sh','editorial/create_briefs.sh','content/write_articles.sh','content/write_video_scripts.sh','review/check_content.sh','publishing/prepare_package.sh','reporting/summarize_run.sh']
 for path in expected:
  text=Path(path).read_text();require(text.startswith('#!/usr/bin/env bash') and len(text.splitlines())>=4,path+' is not implemented')
  subprocess.run(['bash','-n',path],check=True,capture_output=True)
 dates=[];run_results=[]
 for rid in RUNS:
  r=Path('runs')/rid;meta=read(r/'run.json');dates.append(meta['as_of_date'])
  require(meta['mode']=='live','Submitted run must be live')
  for name in ['project.json','sources.json','editorial_policy.md']:require((r/'config'/name).is_file(),'Missing exact configuration snapshot '+name)
  for name in ['select_items.md','create_briefs.md','write_articles.md','write_video_scripts.md']:require((r/'prompts'/name).is_file(),'Missing actual prompt '+name)
  items={(x['item_id'],x['version_id']):x for x in rows(r/'eligible.jsonl')}
  unique={x.get('underlying_id',x['item_id']):x for x in items.values()};kinds=collections.Counter(x['kind'] for x in unique.values())
  require(len(unique)>=12 and len({x['publisher_id'] for x in unique.values()})>=6,'Coverage below minimum')
  require(all(kinds[k]>=2 for k in ['feed','youtube','podcast']),'Input-type minimum not met')
  end=datetime.date.fromisoformat(meta['as_of_date']);start=end-datetime.timedelta(days=29)
  for x in unique.values():require(start<=datetime.datetime.fromisoformat(x['published_at'].replace('Z','+00:00')).date()<=end,'Out-of-window eligible item')
  decisions=rows(r/'decisions.jsonl');require({(d['item_id'],d['version_id']) for d in decisions}==set(items),'Each eligible item needs a decision')
  by_piece=[]
  for b in rows(r/'briefs.jsonl'):
   publishers=set();refs=0
   for claim in b['claims']:
    require(claim['type'] in ['reported_fact','source_claim','inference'] and claim['evidence'],'Missing claim type or evidence')
    for ref in claim['evidence']:
     x=items[(ref['item_id'],ref['version_id'])];publishers.add(x['publisher_id']);refs+=1
     require(Path(x['text_path']).is_file(),'Missing cited text asset')
     if ref['locator']['type']=='text':require(ref['locator']['quote'] in Path(x['text_path']).read_text(),'Non-resolving exact quotation')
     else:
      segments=read(Path(x['segments_path']));require(any(s['segment_id']==ref['locator']['segment_id'] for s in segments),'Non-resolving timestamp locator')
   require(len(publishers)>=3,'Fewer than three publishers for piece '+b['piece_id'])
   by_piece.append({'piece_id':b['piece_id'],'publishers':sorted(publishers),'evidence_references':refs})
  run_results.append({'run_id':rid,'date':meta['as_of_date'],'eligible':len(unique),'input_types':dict(kinds),'pieces':by_piece})
 require(len(set(dates))==2,'Two different real dates required')
 latest=Path('runs')/RUNS[-1];sample=read(latest/'student_review/student_responses.json')
 require(sample['status']=='completed' and len(sample['sample'])>=6,'Student review not recorded complete')
 initial=collections.Counter(x['ai_decision']['decision'] for x in sample['sample'])
 require(initial['accept']>=3 and initial['reject']+initial['defer']>=3,'Review sample does not cover both groups')
 require(read(latest/'approval.json')['review_id']==read(latest/'review.json')['review_id'],'Historical original review/approval mismatch')
 production=read(Path('publishing/production/audience-videos.json'));technical=read(Path('publishing/production/technical-demo.json'))
 require(len(production['videos'])==3 and all(180<=v['final_duration_seconds']<=300 for v in production['videos']),'Audience video duration failure')
 require(240<=technical['duration_seconds']<=360 and technical['publication_url'],'Technical demo duration/link failure')
 links=read(latest/'package/publication_links.json');require(len(links)==3 and all(x['substack_url'] and x['youtube_url'] for x in links),'Missing publication pair')
 for link in links:
  article=Path('publishing/production/published-articles')/(link['piece_id']+'.md');s=article.read_text();body=re.split(r'\n## References',s)[0]
  words=len(re.sub(r'\[([^]]+)\]\([^)]+\)',r'\1',body).split());require(600<=words<=900,'Published article outside length range')
  require(link['youtube_url'] in s,'Missing article-to-video link')
  description=Path('publishing/production')/(link['piece_id']+'-youtube-description.txt');require(link['substack_url'] in description.read_text(),'Missing video-to-article link')
  link['article_words_approx']=words
 # Execute real store/filter stages against retained records in a disposable root.
 with tempfile.TemporaryDirectory(prefix='beyond-target-replay-') as temp:
  temp=Path(temp)
  for name in ['lib/common.py','data/store.py','data/store.sh','processing/filter_items.py','processing/filter_items.sh']:
   (temp/name).parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,temp/name)
  (temp/'runs/replay').mkdir(parents=True);(temp/'runs/replay/run.json').write_text(json.dumps({'as_of_date':dates[-1],'mode':'replay'}))
  run_stage(temp,['data/store.sh','init'])
  prior=(ROOT/'runs'/RUNS[0]/'corpus.jsonl').read_text();run_stage(temp,['data/store.sh','upsert','runs/replay'],prior)
  second=(ROOT/'runs'/RUNS[1]/'items.jsonl').read_text();updates=run_stage(temp,['data/store.sh','upsert','runs/replay'],second)
  replay=run_stage(temp,['data/store.sh','upsert','runs/replay'],second)
  require(all(x['change']=='unchanged' for x in replay),'Same-input replay created new/changed records')
  expected_new={x['item_id'] for x in rows(ROOT/'runs'/RUNS[1]/'changes.jsonl') if x['change']=='new'}
  require({x['item_id'] for x in updates if x['change']=='new'}==expected_new,'New discoveries do not reproduce from first-day corpus')
  corpus=run_stage(temp,['data/store.sh','list']);filtered=run_stage(temp,['processing/filter_items.sh','runs/replay'],''.join(json.dumps(x)+'\n' for x in corpus))
  require({(x['item_id'],x['version_id']) for x in filtered}==set((x['item_id'],x['version_id']) for x in rows(ROOT/'runs'/RUNS[1]/'eligible.jsonl')),'Offline freshness result differs from retained second day')
  replay_result={'label':'Offline replay on a temporary reconstructed metadata index; not a new live day or fresh model inference','second_day_changes':dict(collections.Counter(x['change'] for x in updates)),'identical_replay':dict(collections.Counter(x['change'] for x in replay)),'eligible_after_replay':len(filtered),'exclusions':dict(collections.Counter(x['reason'] for x in rows(temp/'runs/replay/exclusions.jsonl'))),'source_item_ids_new':sorted(expected_new),'production_unchanged':True}
 failed=Path('runs/20261015T161648Z-66e801/logs');failures=[read(p) for p in failed.glob('*.json') if read(p).get('status')=='failed']
 require(any('resolve' in str(x.get('errors',[])).lower() for x in failures),'Retained real DNS failure evidence missing')
 return {'checked_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'passed':True,'required_scripts':16,'runs':run_results,'publication_pairs':links,'technical_demo_duration_seconds':technical['duration_seconds'],'isolated_replay':replay_result,'failure_receipts':len(failures),'scope':'Offline structural/reference/replay verification, not a grade, a fresh live collection, a factual audio audit, or independent web access test','evidence_scope':'Cited excerpts preserve original version identifiers; historical approval applies to the original full local archive, not the exported file bytes.'}
def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',default='-');args=parser.parse_args()
 try:result=inspect()
 except (AssertionError,KeyError,ValueError,FileNotFoundError,subprocess.CalledProcessError) as e:
  print(json.dumps({'passed':False,'error':str(e)},indent=2));return 1
 text=json.dumps(result,indent=2,ensure_ascii=False)+'\n'
 if args.output=='-':print(text,end='')
 else:Path(args.output).write_text(text);print('Passed; report saved to '+args.output)
 return 0
if __name__=='__main__':sys.exit(main())

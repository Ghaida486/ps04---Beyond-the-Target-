"""Fictional contract fixtures. These are not live assignment evidence."""
import unittest, tempfile, shutil, subprocess, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def dump(p,x): p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(x))
def stream(p,x): p.parent.mkdir(parents=True,exist_ok=True); p.write_text(''.join(json.dumps(v)+'\n' for v in x))
class Contracts(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.root=Path(self.tmp.name)/'repo'
        shutil.copytree(ROOT,self.root,ignore=shutil.ignore_patterns('.git','.env*','__pycache__','runs','evidence','media','.venv','work','models'))
        self.run=self.root/'runs/fixture'; self.run.mkdir(parents=True); (self.run/'logs').mkdir()
        dump(self.run/'run.json',{'run_id':'fixture','as_of_date':'2026-10-14','started_at':'2026-10-14T00:00:00Z','mode':'example','previous_run_id':None})
    def tearDown(self): self.tmp.cleanup()
    def call(self,script,args=(),records=None):
        return subprocess.run(['bash',script,*args],cwd=self.root,input=''.join(json.dumps(v)+'\n' for v in records) if records is not None else None,text=True,capture_output=True)
    def item(self,n=0):
        return {'item_id':'item'+str(n),'version_id':'v1','source_id':'s'+str(n),'publisher_id':'p'+str(n%6),'kind':('feed','youtube','podcast')[n%3],'title':'Fictional fixture '+str(n),'url':'https://example.invalid/'+str(n),'published_at':'2026-10-01T00:00:00Z','retrieved_at':'2026-10-14T00:00:00Z','media_url':None,'text_path':'data/assets/'+str(n)+'.txt','segments_path':None if n%3==0 else 'data/assets/'+str(n)+'.json'}
    def test_store_duplicate_and_versions(self):
        x=self.item(); y=dict(x,retrieved_at='2026-10-14T12:00:00Z'); z=dict(x,version_id='v2')
        r=self.call('data/store.sh',['upsert','runs/fixture'],[x,y,z,z]); self.assertEqual(r.returncode,0,r.stderr)
        self.assertEqual([v['change'] for v in map(json.loads,r.stdout.splitlines())],['new','unchanged','changed','unchanged'])
        r=self.call('data/store.sh',['get',x['item_id'],'v1']); self.assertEqual(json.loads(r.stdout)['version_id'],'v1')
        r=self.call('data/store.sh',['list']); self.assertEqual(len(r.stdout.splitlines()),1); self.assertEqual(json.loads(r.stdout)['version_id'],'v2')
    def test_inclusive_window_and_exclusions(self):
        dates=['2026-09-15T00:00:00Z','2026-09-14T23:59:59Z','2026-10-14T23:59:59Z','2026-10-15T00:00:00Z',None,'nonsense']
        r=self.call('processing/filter_items.sh',['runs/fixture'],[dict(self.item(n),published_at=d) for n,d in enumerate(dates)])
        self.assertEqual(r.returncode,0,r.stderr); self.assertEqual(len(r.stdout.splitlines()),2)
        reasons={v['reason'] for v in map(json.loads,(self.run/'exclusions.jsonl').read_text().splitlines())}
        self.assertEqual(reasons,{'outside_window','future_date','unknown_date','invalid_date'})
    def fixture(self):
        items=[self.item(n) for n in range(12)]; decisions=[]
        for x in items:
            p=self.root/x['text_path']; p.parent.mkdir(parents=True,exist_ok=True); p.write_text('Exact fictional supporting passage.')
            if x['segments_path']: dump(self.root/x['segments_path'],[{'segment_id':'1','start_seconds':0,'end_seconds':5,'text':'Exact fictional supporting passage.'}])
            decisions.append({'item_id':x['item_id'],'version_id':x['version_id'],'decision':'accept','reason':'Fictional test','piece_ids':['01','02','03']})
        briefs=[]; manifests={'articles':[],'video_scripts':[]}
        for p in ('01','02','03'):
            claims=[]
            for n,x in enumerate(items[:3]):
                locator={'type':'text','quote':'Exact fictional supporting passage.'} if x['kind']=='feed' else {'type':'segment','segment_id':'1'}
                claims.append({'claim_id':p+'-c'+str(n),'statement':'Fictional test claim','type':'source_claim','evidence':[{'item_id':x['item_id'],'version_id':x['version_id'],'locator':locator}]})
            briefs.append({'piece_id':p,'title':p,'question':'Fictional','argument':'Distinct argument '+p,'synthesis':'Fictional connection','limitations':'Fictional limitation','claims':claims})
            for kind in manifests:
                path=Path('runs/fixture')/kind/(p+'.md'); (self.root/path).parent.mkdir(parents=True,exist_ok=True); (self.root/path).write_text('As of: 2026-10-14\n'+ ' '.join(c['claim_id'] for c in claims)+'\nhttps://example.invalid/')
                manifests[kind].append({'piece_id':p,'path':str(path),'claim_ids':[c['claim_id'] for c in claims]})
        stream(self.run/'eligible.jsonl',items); stream(self.run/'decisions.jsonl',decisions); stream(self.run/'briefs.jsonl',briefs)
        for kind,values in manifests.items(): stream(self.run/(kind+'.jsonl'),values)
    def test_review_and_stale_approval(self):
        self.fixture(); r=self.call('review/check_content.sh',['runs/fixture']); self.assertEqual(r.returncode,0,r.stderr)
        review=json.loads(r.stdout); self.assertTrue(review['passed'],review['issues']); dump(self.run/'review.json',review)
        # Synthetic test-only approval. Not a student review and never an assignment artifact.
        dump(self.run/'approval.json',{'review_id':review['review_id'],'decision':'approve','reviewer':'FICTIONAL TEST','reviewed_at':'2026-10-14T00:00:00Z','notes':'Fixture assertion only'})
        r=self.call('publishing/prepare_package.sh',['runs/fixture']); self.assertEqual(r.returncode,0,r.stderr)
        links=self.run/'package/publication_links.json'; entered=json.loads(links.read_text()); entered[0]['substack_url']='https://example.invalid/test'; dump(links,entered)
        r=self.call('publishing/prepare_package.sh',['runs/fixture']); self.assertEqual(r.returncode,0,r.stderr); self.assertEqual(json.loads(links.read_text())[0]['substack_url'],'https://example.invalid/test')
        with (self.run/'articles/01.md').open('a') as f: f.write('\nChanged after approval')
        r=self.call('publishing/prepare_package.sh',['runs/fixture']); self.assertEqual(r.returncode,1); self.assertIn('stale',r.stderr)
    def test_missing_content_assessment_completes_but_fails(self):
        r=self.call('review/check_content.sh',['runs/fixture']); self.assertEqual(r.returncode,0,r.stderr); self.assertFalse(json.loads(r.stdout)['passed'])
    def test_failed_collector_records_incomplete(self):
        dump(self.run/'config/sources.json',[{'source_id':'broken','publisher_id':'fiction','kind':'feed','url':'file:///nonexistent/fictional-feed.xml'}])
        r=self.call('collectors/fetch_feeds.sh',['runs/fixture']); self.assertEqual(r.returncode,1)
        receipt=json.loads(next((self.run/'logs').glob('fetch_feeds-*.json')).read_text()); self.assertEqual(receipt['status'],'failed'); self.assertTrue(receipt['errors'])
    def test_codex_provider_removes_api_credentials_and_saves_json(self):
        import os
        binary=self.root/'test-bin/codex'; binary.parent.mkdir()
        binary.write_text("#!/usr/bin/env python3\nimport os,sys,json\nassert 'OPENAI_API_KEY' not in os.environ\nassert 'CODEX_API_KEY' not in os.environ\nargs=sys.argv\nassert '--sandbox' in args and args[args.index('--sandbox')+1]=='read-only'\nassert '--ignore-user-config' in args\ntext=sys.stdin.read()\nassert 'Return exactly' in text\nopen(args[args.index('--output-last-message')+1],'w').write('{\"ok\":true}')\nprint(json.dumps({'type':'turn.completed','usage':{'input_tokens':1,'output_tokens':1}}))\n")
        binary.chmod(0o755)
        env=os.environ.copy(); env['PATH']=str(binary.parent)+os.pathsep+env['PATH']; env['OPENAI_API_KEY']='FICTIONAL-TEST-SENTINEL'; env['CODEX_API_KEY']='FICTIONAL-TEST-SENTINEL'
        r=subprocess.run(['python3','tools/check_ai.py'],cwd=self.root,capture_output=True,text=True,env=env)
        self.assertEqual(r.returncode,0,r.stderr)
        report=json.loads((self.root/'docs/ai_connection_check.json').read_text()); self.assertFalse(report['uses_openai_api_key'])
        receipt=json.loads(next((self.root/'work/connection-check/logs').glob('*.json')).read_text()); self.assertIsNone(receipt['cost_usd'])
        saved=list((self.root/'work/connection-check/model_calls').glob('*response.json')); self.assertEqual(len(saved),1)

    def test_aggregator_resolves_original_and_stable_identity(self):
        dump(self.run/'config/sources.json',[{'source_id':'news','publisher_id':'origin','kind':'feed','url':'https://www.bing.com/news/search?format=rss','aggregator':'bing_news','allowed_hosts':['original.example']}])
        program="""import sys
sys.path[:0]=['lib','collectors']
import feed_support
feed_support.get=lambda url: b'<rss><channel><item><title>Women compete</title><link>https://www.bing.com/news/apiclick?url=https%3A%2F%2Foriginal.example%2Fstory</link><guid>temporary-id</guid><pubDate>Wed, 14 Oct 2026 12:00:00 GMT</pubDate></item><item><title>Duplicate route</title><link>https://www.bing.com/news/apiclick?url=https%3A%2F%2Foriginal.example%2Fstory</link><guid>different-temporary-id</guid><pubDate>Wed, 14 Oct 2026 12:00:00 GMT</pubDate></item></channel></rss>'
sys.exit(feed_support.collect('runs/fixture','feed'))
"""
        r=subprocess.run(['python3','-c',program],cwd=self.root,capture_output=True,text=True)
        self.assertEqual(r.returncode,0,r.stderr); values=[json.loads(x) for x in r.stdout.splitlines()]
        self.assertEqual(values[0]['url'],'https://original.example/story')
        self.assertEqual(values[0]['item_id'],values[1]['item_id']); self.assertEqual(values[0]['publisher_id'],'origin')

    def test_article_body_excludes_navigation_and_rejects_nav_only(self):
        program="""import sys
sys.path.insert(0,'processing')
from written_text import extract_article
body=' '.join(['substantive']*110)
a='<nav>new headlines</nav><div class="post-entry"><p>'+body+'</p><aside>unrelated promotion</aside></div>'
b=a.replace('new headlines','different navigation and new recommendations')
assert extract_article(a)==extract_article(b)==body
try: extract_article('<nav><p>'+body+'</p></nav>')
except RuntimeError: pass
else: raise AssertionError('Navigation was accepted as article evidence')
"""
        r=subprocess.run(['python3','-c',program],cwd=self.root,capture_output=True,text=True); self.assertEqual(r.returncode,0,r.stderr)

    def test_student_review_preserves_entered_judgment(self):
        self.fixture()
        (self.run/'config').mkdir(exist_ok=True)
        shutil.copyfile(self.root/'config/editorial_policy.md',self.run/'config/editorial_policy.md')
        r=subprocess.run(['python3','tools/prepare_review.py','runs/fixture'],cwd=self.root,capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stderr)
        path=self.run/'student_review/student_responses.json';form=json.loads(path.read_text());form['reviewer']='FICTIONAL TEST STUDENT';form['sample'][0]['student_judgment']='agree';form['sample'][0]['student_reason']='A test response, not assignment evidence';dump(path,form)
        saved=path.read_bytes();worksheet=(self.run/'student_review/worksheet.md').read_bytes()
        r=subprocess.run(['python3','tools/prepare_review.py','runs/fixture'],cwd=self.root,capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stderr)
        self.assertEqual(path.read_bytes(),saved);self.assertEqual((self.run/'student_review/worksheet.md').read_bytes(),worksheet);self.assertFalse((self.run/'approval.json').exists())

    def test_insufficient_evidence_does_not_call_model(self):
        stream(self.run/'eligible.jsonl',[])
        r=self.call('editorial/create_briefs.sh',['runs/fixture'],[]); self.assertEqual(r.returncode,1); self.assertIn('Evidence gate',r.stderr); self.assertFalse((self.run/'model_calls').exists())
if __name__=='__main__': unittest.main()

"""The public evidence export must never masquerade as complete cached media."""
import json,subprocess,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class PublicExcerptCache(unittest.TestCase):
 def reuse(self,text,segments):
  with tempfile.TemporaryDirectory() as folder:
   folder=Path(folder);(folder/'text.txt').write_text(text);(folder/'segments.json').write_text(json.dumps(segments))
   item={'text_path':str(folder/'text.txt'),'segments_path':str(folder/'segments.json')}
   program="import sys,json;sys.path[:0]=['processing','lib'];from extract_content import retained_media_complete;print(json.dumps(retained_media_complete("+repr(item)+")))"
   result=subprocess.run(['python3','-c',program],cwd=ROOT,text=True,capture_output=True)
   self.assertEqual(result.returncode,0,result.stderr);return json.loads(result.stdout)
 def test_excerpt_and_provenance_exports_are_not_reusable_transcripts(self):
  segment=[{'start_seconds':0,'end_seconds':3,'text':'Quoted sample'}]
  self.assertFalse(self.reuse('PUBLIC EVIDENCE EXCERPT — partial source\nQuoted sample',segment))
  self.assertFalse(self.reuse('PUBLIC PROVENANCE RECORD — no transcript',[]))
 def test_complete_retained_transcript_can_be_reused_but_empty_one_cannot(self):
  self.assertTrue(self.reuse('Complete retained transcript',[{'start_seconds':0,'end_seconds':3,'text':'Complete retained transcript'}]))
  self.assertFalse(self.reuse('No decoded speech',[]))
if __name__=='__main__':unittest.main()

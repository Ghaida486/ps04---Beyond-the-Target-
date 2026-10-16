"""Tamper tests: a broken exported submission must not receive a passing report."""
import json, shutil, subprocess, tempfile, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class SubmissionIntegrity(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)/'repo'
  shutil.copytree(ROOT,self.root,ignore=shutil.ignore_patterns('.git','__pycache__','.venv','work','models','media'))
 def tearDown(self):self.temp.cleanup()
 def verify_fails(self,message):
  result=subprocess.run(['python3','tools/verify_submission.py'],cwd=self.root,text=True,capture_output=True)
  self.assertEqual(result.returncode,1,result.stderr)
  data=json.loads(result.stdout);self.assertFalse(data['passed']);self.assertIn(message,data['error'])
 def test_missing_real_claim_passage_cannot_pass(self):
  run=self.root/'runs/20261015T161701Z-ddbccc'
  item=next(x for x in map(json.loads,(run/'eligible.jsonl').read_text().splitlines()) if x['version_id']=='6b913619daa120163d5cc4b59a24a5b2d24c2409d6eb8147ba86ec2b6de73c7d')
  (self.root/item['text_path']).unlink();self.verify_fails('Missing retained asset path')
 def test_missing_persistent_index_cannot_pass(self):
  (self.root/'data/evidence/index.sqlite3').unlink()
  self.verify_fails('Persistent evidence index missing')
 def test_missing_prompt_snapshot_cannot_pass(self):
  (self.root/'runs/20261015T161701Z-ddbccc/prompts/select_items.md').unlink()
  self.verify_fails('Missing actual prompt')
 def test_changed_student_approval_is_not_silently_accepted(self):
  path=self.root/'runs/20261015T161701Z-ddbccc/approval.json';data=json.loads(path.read_text());data['review_id']='TAMPERED-TEST-ONLY';path.write_text(json.dumps(data))
  self.verify_fails('Historical original review/approval mismatch')
if __name__=='__main__':unittest.main()

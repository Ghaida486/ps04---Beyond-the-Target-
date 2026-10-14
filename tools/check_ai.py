"""One tiny inference using ChatGPT login; not a homework pipeline run."""
import sys,tempfile,shutil
sys.path.insert(0,'lib')
from common import *
def main():
    path=Path('work/connection-check'); path.mkdir(parents=True,exist_ok=True)
    shutil.copytree('config',path/'config',dirs_exist_ok=True)
    (path/'prompts').mkdir(exist_ok=True)
    (path/'prompts/check.md').write_text('Return exactly the JSON object {"ok":true}. This is a connection check. Do not use tools.')
    stage=Stage(path,'check_ai')
    try:
        result=model(path,stage,'check',{})
        if result!={'ok':True}: raise ValueError('Unexpected check response')
        stage.output=1; stage.finish()
        safe={'checked_at':now(),'provider':'codex_cli','status':'passed','uses_openai_api_key':False,'purpose':'Connection check only; not an assignment run'}
        write('docs/ai_connection_check.json',safe); emit(safe); return 0
    except Exception as e:
        stage.error(e); return stage.finish(1)
invoke(main)

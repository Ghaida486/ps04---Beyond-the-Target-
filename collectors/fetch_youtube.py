import sys
sys.path.insert(0,'lib')
from common import *
import subprocess

def main():
    if len(sys.argv)!=2: return 2
    run=Path(sys.argv[1]); stage=Stage(run,'fetch_youtube'); stage.tools.append('yt-dlp'); errors=False
    sources=[s for s in read(run/'config/sources.json') if s['kind']=='youtube']; stage.input=len(sources)
    if not sources: stage.error('No youtube sources configured'); errors=True
    for source in sources:
        try:
            result=subprocess.run(['yt-dlp','--dump-json','--skip-download','--playlist-end',str(source.get('max_items',8)),source['url']],capture_output=True,text=True,timeout=240)
            if result.returncode: stage.error(f'{source["source_id"]}: yt-dlp failed: {result.stderr[-600:]}'); errors=True
            for line in result.stdout.splitlines():
                x=json.loads(line); date=x.get('upload_date'); published=dt.datetime.strptime(date,'%Y%m%d').replace(tzinfo=dt.timezone.utc).isoformat().replace('+00:00','Z') if date else None
                record={'item_id':'youtube-'+x['id'],'source_id':source['source_id'],'publisher_id':source['publisher_id'],'kind':'youtube','title':x['title'],'url':'https://www.youtube.com/watch?v='+x['id'],'published_at':published,'retrieved_at':now(),'media_url':None,'underlying_id':source.get('identity_overrides',{}).get(x['id'],'youtube-'+x['id']),'native_id':x['id']}
                for key in ('transcription_model','transcription_task'):
                    if key in source: record[key]=source[key]
                emit(record); stage.output+=1
        except Exception as e: stage.error(f'{source["source_id"]}: {e}'); errors=True
    return stage.finish(1 if errors else 0)
invoke(main)

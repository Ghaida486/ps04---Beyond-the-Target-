import sys
sys.path.insert(0,'lib')
from common import *
import subprocess
import re
from html.parser import HTMLParser
import html
from written_text import extract_article

class Text(HTMLParser):
    def __init__(self): super().__init__(); self.parts=[]; self.hidden=0
    def handle_starttag(self,tag,attrs):
        if tag in ('script','style','noscript'): self.hidden+=1
        if tag in ('p','h1','h2','h3','li','br'): self.parts.append('\n')
    def handle_endtag(self,tag):
        if tag in ('script','style','noscript'): self.hidden=max(0,self.hidden-1)
    def handle_data(self,data):
        if not self.hidden: self.parts.append(data)
def transcript(path):
    if path.suffix=='.json':
        raw=read(path); events=raw.get('events',[]); values=[]
        for e in events:
            text=''.join(s.get('utf8','') for s in e.get('segs',[])).strip()
            if text: values.append({'segment_id':str(len(values)+1),'start_seconds':e['tStartMs']/1000,'end_seconds':(e['tStartMs']+e.get('dDurationMs',0))/1000,'text':text})
        return values
    values=[]; content=path.read_text()
    pat=r'(\d{2}:\d{2}:\d{2}\.\d{3}) --> (\d{2}:\d{2}:\d{2}\.\d{3})[^\n]*\n(.*?)(?=\n\s*\n|\Z)'
    def seconds(x):
        h,m,s=x.split(':'); return int(h)*3600+int(m)*60+float(s)
    for a,b,t in re.findall(pat,content,re.S):
        t=html.unescape(re.sub('<[^>]+>','',t)).strip()
        if t: values.append({'segment_id':str(len(values)+1),'start_seconds':seconds(a),'end_seconds':seconds(b),'text':t})
    return values

def transcribe(audio,stage,settings=None):
    """Local speech recognition only. No audio is sent to a paid API."""
    import subprocess
    project=read(stage.run/'config/project.json')
    python=ROOT/'.venv/bin/python'
    if not python.exists(): raise RuntimeError('Local transcription environment missing; see SETUP.md')
    output=audio.parent/'local-transcript.json'
    if output.exists():
        stage.tools.append('reused-retained-local-transcript')
        return read(output)
    settings=settings or {}
    name=settings.get('transcription_model',project.get('transcription_model','base.en'))
    task=settings.get('transcription_task','transcribe')
    stage.tools.append('faster-whisper:'+name)
    result=subprocess.run([str(python),'processing/transcribe_local.py',str(audio),str(output),name,task],capture_output=True,text=True,timeout=3600)
    if result.returncode: raise RuntimeError('Local transcription failed: '+result.stderr[-600:])
    return read(output)

def main():
    if len(sys.argv)!=2: return 2
    run=Path(sys.argv[1]); stage=Stage(run,'extract_content'); values=rows(); stage.input=len(values); errors=False
    # The persistent index is accessed exclusively through the store interface.
    stored=subprocess.run(['bash','data/store.sh','list'],capture_output=True,text=True,check=True)
    cache={x['item_id']:x for x in map(json.loads,stored.stdout.splitlines())}; reuse=[]
    retained={}
    for provenance in Path('data/media').glob('*/source.json'):
        old_source=read(provenance)
        retained[old_source['item_id']]=(old_source,provenance.parent)
    for item in values:
        try:
            print('Extracting: '+item['title'],file=sys.stderr,flush=True)
            if eligible_reason(item['published_at'],dt.date.fromisoformat(read(run/'run.json')['as_of_date'])):
                # Dates are filtered formally after storage; avoid downloading old large media.
                if item['kind']!='feed':
                    reuse.append({'item_id':item['item_id'],'status':'skipped_before_extraction','reason':'publication date not eligible'}); continue
            old=cache.get(item['item_id'])
            if old and item['kind'] in ('youtube','podcast') and all(old.get(k)==item.get(k) for k in ('title','published_at','url','media_url','underlying_id')) and Path(old['text_path']).exists() and Path(old['segments_path']).exists():
                emit(dict(old,retrieved_at=item['retrieved_at'])); stage.output+=1; reuse.append({'item_id':item['item_id'],'status':'reused_unchanged_media'}); continue
            work=ROOT/'data/media'/digest([item['item_id'],item['retrieved_at']])[:24]; work.mkdir(parents=True,exist_ok=True)
            segments=None
            prior=retained.get(item['item_id'])
            if item['kind']!='feed' and prior and all(prior[0].get(k)==item.get(k) for k in ('title','published_at','url','media_url')):
                work=prior[1]
                item['content_retrieved_at']=prior[0]['retrieved_at']
            else:
                write(work/'source.json',item)
            if item['kind']=='feed':
                content=get(item['url']); (work/'source.html').write_bytes(content)
                source_html=content.decode('utf-8',errors='replace')
                # Prefer the originating article's publication metadata over an aggregator's date.
                original_dates=re.findall(r'"datePublished"\s*:\s*"([^"\n]+)"',source_html)
                if original_dates:
                    try:
                        original=dt.datetime.fromisoformat(original_dates[0].replace('Z','+00:00'))
                        if original.tzinfo is not None:
                            item['published_at']=original.astimezone(dt.timezone.utc).isoformat().replace('+00:00','Z')
                            item['publication_date_basis']='originating article datePublished; feed date retained separately'
                    except ValueError: pass
                from bs4 import BeautifulSoup
                source_soup=BeautifulSoup(source_html,'html.parser')
                if not original_dates:
                    date_node=source_soup.select_one('h3.date')
                    if date_node:
                        try:
                            source_day=dt.datetime.strptime(date_node.get_text(strip=True),'%B %d, %Y').date()
                            item['published_at']=source_day.isoformat()+'T00:00:00Z'
                            item['publication_date_basis']='originating visible calendar date; UTC midnight is a day-precision normalization, not a known publication time'
                            item['publication_time_precision']='day'
                        except ValueError: pass
                canonical=source_soup.find('link',rel='canonical')
                if canonical and canonical.get('href'): item['url']=canonical['href']
                heading=source_soup.select_one('h1.articleTitle') or source_soup.find('h1')
                if heading and heading.get_text(strip=True): item['title']=heading.get_text(' ',strip=True)
                text=extract_article(source_html)
                # Require substantive content; headlines/abstract-only pages are insufficient.
                if len(text.split())<100: raise RuntimeError('Source has fewer than 100 extracted words; inspect access/full text')
            elif item['kind']=='youtube':
                stage.tools.append('yt-dlp')
                result=subprocess.run(['yt-dlp','--no-playlist','-f','bestaudio','--write-subs','--write-auto-subs','--sub-langs','en.*','--sub-format','json3/vtt','-o',str(work/'source.%(ext)s'),item['url']],capture_output=True,text=True,timeout=360)
                if result.returncode:
                    # A caption 429 must not prevent a separate audio download/local transcription.
                    write(work/'caption_failure.json',{'error':result.stderr[-1000:],'recorded_at':now()})
                    retry=subprocess.run(['yt-dlp','--no-playlist','-f','bestaudio','--socket-timeout','20','--retries','1','-o',str(work/'source.%(ext)s'),item['url']],capture_output=True,text=True,timeout=360)
                    if retry.returncode: raise RuntimeError('yt-dlp audio fallback failed: '+retry.stderr[-350:])
                    stage.tools.append('caption-failure-recovered-by-local-transcription')
                captions=list(work.glob('*.json3'))+list(work.glob('*.vtt'))
                if captions:
                    path=captions[0]
                    if path.suffix=='.json3':
                        tmp=path.with_suffix('.json'); tmp.write_bytes(path.read_bytes()); path=tmp
                    try: segments=transcript(path)
                    except (ValueError,KeyError): segments=None
                if not segments:
                    audio=next(p for p in work.glob('source.*') if p.suffix not in ('.vtt','.json','.json3','.part'))
                    segments=transcribe(audio,stage,item)
                text='\n'.join(x['text'] for x in segments)
            else:
                if not item.get('media_url'): raise RuntimeError('Podcast audio enclosure missing')
                audio=work/'source.audio'
                if not audio.exists(): audio.write_bytes(get(item['media_url']))
                segments=transcribe(audio,stage,item); text='\n'.join(x['text'] for x in segments)
            if not text.strip(): raise RuntimeError('No substantive evidence extracted')
            transcript_meta=work/'local-transcript.metadata.json'
            if transcript_meta.exists(): item['transcript_provenance']=read(transcript_meta)
            metadata={k:item.get(k) for k in ('title','url','published_at','publisher_id','kind','media_url','underlying_id','transcript_provenance')}
            version=digest({'metadata':metadata,'text':text,'segments':segments})
            assets=ROOT/'data/assets'/digest(item['item_id'])[:24]/version; assets.mkdir(parents=True,exist_ok=True)
            (assets/'text.txt').write_text(text)
            if segments is not None: write(assets/'segments.json',segments)
            emit(dict(item,version_id=version,text_path=relative(assets/'text.txt'),segments_path=relative(assets/'segments.json') if segments is not None else None,retained_media_dir=relative(work))); stage.output+=1
        except Exception as e: stage.error(f'{item["item_id"]}: {e}'); errors=True
    write(run/'extraction_cache.json',reuse); return stage.finish(1 if errors else 0)
invoke(main)

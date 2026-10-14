"""RSS/Atom parsing shared by written and podcast collectors."""
import sys
sys.path.insert(0,'lib')
from common import *
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from urllib.parse import urljoin, urlsplit, parse_qs
import re

def tag(el,name):
    return next((x for x in el.iter() if x.tag.rsplit('}',1)[-1]==name),None)
def val(el,name):
    x=tag(el,name); return (x.text or '').strip() if x is not None else ''
def date(raw):
    if not raw: return None
    try:
        try: d=parsedate_to_datetime(raw)
        except (ValueError,TypeError): d=dt.datetime.fromisoformat(raw.replace('Z','+00:00'))
        if d.tzinfo is None: d=d.replace(tzinfo=dt.timezone.utc)
        return d.astimezone(dt.timezone.utc).isoformat().replace('+00:00','Z')
    except (ValueError,TypeError): return None

def collect(run,kind):
    stage=Stage(run,'fetch_'+('feeds' if kind=='feed' else 'podcasts')); errors=False
    sources=[s for s in read(Path(run)/'config/sources.json') if s['kind']==kind]; stage.input=len(sources)
    if not sources: stage.error(f'No {kind} sources configured'); errors=True
    for source in sources:
        try:
            root=ET.fromstring(get(source['url'])); entries=[x for x in root.iter() if x.tag.rsplit('}',1)[-1] in ('item','entry')]
            for entry in entries[:source.get('max_items',30)]:
                if source.get('include_title_pattern') and not re.search(source['include_title_pattern'],val(entry,'title'),re.I): continue
                link=val(entry,'link')
                if not link:
                    links=[x for x in entry if x.tag.rsplit('}',1)[-1]=='link' and x.get('rel','alternate')=='alternate']
                    link=links[0].get('href','') if links else ''
                enclosure=tag(entry,'enclosure'); media=enclosure.get('url') if enclosure is not None else None
                if kind=='podcast' and not media: continue
                if not link: link=media or ''
                if not link: continue
                # Aggregators are discovery routes; identity and publisher refer to the original article.
                if source.get('aggregator')=='bing_news':
                    link=parse_qs(urlsplit(link).query).get('url',[link])[0]
                    if urlsplit(link).hostname not in source.get('allowed_hosts',[]): continue
                native=(link if source.get('aggregator') else val(entry,'guid') or val(entry,'id') or link)
                if source['publisher_id']=='world-archery':
                    match=re.search(r'/news/(\d+)/',link)
                    if match: native='world-archery-news-'+match.group(1)
                original_feed_date=date(val(entry,'pubDate') or val(entry,'published') or val(entry,'updated'))
                item={'item_id':kind+'-'+digest([source['publisher_id'],native])[:24],'source_id':source['source_id'],'publisher_id':source['publisher_id'],'kind':kind,'title':val(entry,'title'),'url':urljoin(source['url'],link),'published_at':date(val(entry,'pubDate') or val(entry,'published') or val(entry,'updated')),'retrieved_at':now(),'media_url':media,'underlying_id':digest([source['publisher_id'],native]),'discovered_via':source['url']}
                item['feed_published_at']=original_feed_date
                # Per-source reconciliations are reviewed configuration, never guessed from title similarity.
                overrides=source.get('identity_overrides',{}); item['underlying_id']=overrides.get(native,item['underlying_id'])
                emit(item); stage.output+=1
        except Exception as e: stage.error(f'{source["source_id"]}: {type(e).__name__}: {e}'); errors=True
    return stage.finish(1 if errors else 0)

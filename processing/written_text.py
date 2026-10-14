"""Extract substantive article bodies, excluding navigation and related-story lists."""
from bs4 import BeautifulSoup
import json

def extract_article(html):
    soup=BeautifulSoup(html,'html.parser')
    def bodies(value):
        if isinstance(value,dict):
            body=value.get('articleBody')
            if isinstance(body,str) and len(body.split())>=100: yield body
            for child in value.values(): yield from bodies(child)
        elif isinstance(value,list):
            for child in value: yield from bodies(child)
    for script in soup.find_all('script',type='application/ld+json'):
        try:
            found=list(bodies(json.loads(script.get_text())))
            if found: return ' '.join(BeautifulSoup(max(found,key=len),'html.parser').get_text(' ',strip=True).split())
        except (ValueError,TypeError): pass
    for selector in ('.post-entry','.pageContent .copy','.story_details','.article__field-paragraphs','article','main'):
        node=soup.select_one(selector)
        if node:
            for unwanted in node.select('script,style,nav,aside,form,.related-news,.related-posts,.advertisement'):
                unwanted.decompose()
            paragraphs=[]
            for child in node.find_all(['p','h2','h3','h4','li']):
                text=' '.join(child.get_text(' ',strip=True).split())
                if text and text not in paragraphs: paragraphs.append(text)
            text='\n'.join(paragraphs)
            if len(text.split())>=100: return text
    raise RuntimeError('No supported substantive article body found; inspect source layout/access')

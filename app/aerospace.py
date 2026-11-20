"""Daily fill-in-the-headline trivia from official NASA news, without an API key."""
from datetime import datetime,timedelta,timezone
from email.utils import parsedate_to_datetime
from html import unescape
import re
from urllib.parse import urlparse
from xml.etree import ElementTree
import requests

NASA_FEED='https://www.nasa.gov/news-release/feed/'

def parse_feed(raw):
    if len(raw)>2_000_000 or b'<!DOCTYPE' in raw.upper() or b'<!ENTITY' in raw.upper():raise ValueError('Unsupported RSS document.')
    root=ElementTree.fromstring(raw);items=[]
    for node in root.findall('.//item'):
        title=unescape(' '.join((node.findtext('title') or '').split()))[:250]
        url=(node.findtext('link') or '').strip();host=urlparse(url).hostname or ''
        if not title or urlparse(url).scheme!='https' or not (host=='nasa.gov' or host.endswith('.nasa.gov')):continue
        try:published=parsedate_to_datetime(node.findtext('pubDate') or '')
        except (ValueError,TypeError):continue
        if published.tzinfo is None:published=published.replace(tzinfo=timezone.utc)
        items.append(dict(title=title,url=url,published=published.isoformat(),source='NASA'))
    if not items:raise ValueError('No dated NASA headlines found.')
    return sorted(items,key=lambda i:i['published'],reverse=True)[:30]

def fetch_news():
    try:
        with requests.get(NASA_FEED,headers={'User-Agent':'PersonalMirror/3.0 (personal RSS reader)'},timeout=(8,20),stream=True) as response:
            response.raise_for_status();raw=bytearray()
            for chunk in response.iter_content(65536):
                raw.extend(chunk)
                if len(raw)>2_000_000:raise ValueError('Feed too large')
        return parse_feed(bytes(raw)),None
    except Exception:return None,'NASA news unavailable. Cached headlines are shown when available.'

def daily_trivia(items,now):
    valid=[i for i in items if datetime.fromisoformat(i['published'])<=now]
    if not valid:return None
    recent=[i for i in valid if now-datetime.fromisoformat(i['published'])<=timedelta(days=14)]
    pool=recent[:10] or valid[:10]
    index=now.date().toordinal()%len(pool);item=pool[index]
    words=list(re.finditer(r'\b[A-Za-z][A-Za-z-]{4,}\b',item['title']))
    excluded={'about','after','before','their','these','those','which','media','invites','announces','release','releases','announced'}
    choices=[w for w in words if w.group().lower() not in excluded] or words
    if not choices:
        question='Which agency published this aerospace update?';answer=item['source'];masked=item['title']
    else:
        word=choices[now.date().toordinal()%len(choices)]
        question='Complete this recent aerospace headline:'
        answer=word.group();masked=item['title'][:word.start()]+'________'+item['title'][word.end():]
    return dict(**item,question=question,answer=answer,masked=masked,day=now.date().isoformat(),older=not bool(recent))

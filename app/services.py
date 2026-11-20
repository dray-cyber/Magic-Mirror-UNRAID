"""Weather, assignment checklist, email shipment notices and LCARS styling."""
import copy
import hashlib
import imaplib
import os
import queue
from time import monotonic
import re
import ssl
import threading
import webbrowser
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from email import policy
from email.parser import BytesParser
from email.utils import parsedate_to_datetime, parseaddr
from html.parser import HTMLParser
from urllib.parse import quote, urlparse, parse_qs, unquote
from zoneinfo import ZoneInfo
import requests

EXTRA_DEFAULTS = dict(theme='lcars', zip_code='', units='fahrenheit', completed={},
    email_enabled=False, email_host='imap.gmail.com', email_user='', email_folder='INBOX',
    email_days=30, email_limit=100, show_completed=True)
LAYOUT = {'clock':[.025,.025,.29,.22], 'weather':[.025,.28,.29,.32],
          'notes':[.025,.65,.29,.27], 'agenda':[.34,.025,.31,.90],
          'assignments':[.68,.025,.295,.47], 'shipments':[.68,.54,.295,.385]}
TITLES = [('clock','01 / LOCAL TIME'),('weather','02 / ATMOSPHERIC CONDITIONS'),
          ('agenda','03 / SCHEDULE'),('assignments','04 / ASSIGNMENT LOG'),
          ('shipments','05 / CARGO MANIFEST'),('notes','06 / PERSONAL LOG')]
COLORS = {'clock':'#ffcc99','weather':'#cc99cc','agenda':'#9999ff',
          'assignments':'#ff9966','shipments':'#cc6666','notes':'#ffcc66'}

def clock_text(value, hour24, seconds=False):
    fmt = '%H:%M' if hour24 else '%I:%M'
    if seconds: fmt += ':%S'
    if not hour24: fmt += ' %p'
    rendered = value.strftime(fmt)
    return rendered if hour24 else rendered.lstrip('0')

class HTMLText(HTMLParser):
    def __init__(self):
        super().__init__(); self.parts=[]; self.hidden=0; self.links=[]
    def handle_starttag(self,tag,attrs):
        if tag=='a':
            self.links.extend(v for k,v in attrs if k=='href' and v)
        if tag in ('script','style'): self.hidden += 1
        if tag in ('br','p','div','tr'): self.parts.append('\n')
    def handle_endtag(self,tag):
        if tag in ('script','style'): self.hidden=max(0,self.hidden-1)
        if tag in ('p','div','tr'): self.parts.append('\n')
    def handle_data(self,data):
        if not self.hidden: self.parts.append(data)

def parse_shipment(raw, strict=False, blocked=""):
    """Heuristic notice parser. Never opens links, loads images, or executes HTML."""
    message = BytesParser(policy=policy.default).parsebytes(raw)
    subject = str(message.get('Subject',''))
    sender = str(message.get('From',''))
    address=parseaddr(sender)[1].lower();domain=address.rsplit('@',1)[-1]
    rules=[r.strip().lower().lstrip('@') for r in blocked.split(',') if r.strip()]
    if any(address==r or domain==r or domain.endswith('.'+r) for r in rules):return []
    if str(message.get('X-Spam-Flag','')).strip().upper()=='YES' or str(message.get('X-Spam-Status','')).lower().startswith('yes'):return []
    plain,html = [],[]
    for part in message.walk():
        if part.get_content_disposition() == 'attachment': continue
        try:
            if part.get_content_type() == 'text/plain': plain.append(part.get_content())
            elif part.get_content_type() == 'text/html': html.append(part.get_content())
        except Exception: continue
    parser=HTMLText();parser.feed('\n'.join(html))
    if plain:
        body = '\n'.join(plain)+'\n'+''.join(parser.parts)
    else:
        parser = HTMLText(); parser.feed('\n'.join(html)); body=''.join(parser.parts)
    tracking_links=[]
    for href in parser.links+re.findall(r'https://[^\s<>\"]+',body):
        try:
            # Decode embedded tracking destinations locally; never visit redirects.
            for _ in range(3):
                candidate=urlparse(href);params=parse_qs(candidate.query)
                nested=next((v[0] for k,v in params.items() if k.lower() in ['url','u','redirect','redirecturl','target','destination'] and v and v[0].startswith('https://')),None)
                if not nested:break
                href=nested
            parsed=urlparse(href);host=(parsed.hostname or '').lower()
            if parsed.scheme!='https':continue
            carrier=next((c for domain,c in [('ups.com','UPS'),('usps.com','USPS'),('fedex.com','FedEx'),('dhl.com','DHL')] if host==domain or host.endswith('.'+domain)),None)
            if not carrier:continue
            query=parse_qs(parsed.query)
            for key,values in query.items():
                if key.lower() in ['tracknum','trackingnumber','trackingnumbers','trknbr','tlabels','tracking-id','tracking-id-list','trackingid','awb']:
                    for value in values:
                        for number in re.split(r'[,;\s]+',value):
                            if re.fullmatch(r'[A-Za-z0-9]{10,34}',number):tracking_links.append((carrier,number.upper()))
        except (ValueError,TypeError):continue
    text = subject+'\n'+body[:150000]
    if not tracking_links and not re.search(r'\b(shipped|shipment|tracking|out for delivery|package|parcel|delivered|in transit|on its way|on the way|arriving|dispatched)\b',text,re.I):
        return []
    def status_of(text):
        if re.search(r'\b(delayed|delivery exception|delivery failed|not delivered|unable to deliver)\b',text,re.I): return 'Delivery issue'
        if re.search(r'\b(out for delivery|arriving today)\b',text,re.I): return 'Out for delivery'
        if re.search(r'\b(was delivered|has been delivered|successfully delivered|delivered to)\b',text,re.I): return 'Delivered'
        if re.search(r'^.{0,60}\bdelivered\b',text,re.I) and not re.search(r'\b(will|when|once|be|estimated|expected)\b',text,re.I): return 'Delivered'
        if re.search(r'\b(shipped|dispatched|in transit|on its way|on the way|has left|picked up by)\b',text,re.I): return 'In transit'
        return None
    status = status_of(subject) or status_of(body[:3000]) or 'Shipping notice'
    numbers = list(tracking_links)
    for match in re.finditer(r'\b1Z[A-Z0-9]{16}\b',text,re.I): numbers.append(('UPS',match.group(0).upper()))
    for match in re.finditer(r'\bTBA\d{10,16}\b',text,re.I): numbers.append(('Amazon',match.group(0).upper()))
    # Long numeric IDs are accepted only with an explicit tracking label.
    for match in re.finditer(r'\btracking(?:\s+(?:number|no\.?|id))?\s*[:#-]?\s*(\d[\d -]{10,32}\d)',text,re.I):
        number = re.sub(r'\D','',match.group(1))
        if len(number) in (20,22) and number.startswith('9'): numbers.append(('USPS',number))
        elif len(number) in (12,15,20,22) and 'fedex' in text.lower(): numbers.append(('FedEx',number))
    # Some carriers print a number below a carrier-specific heading without 'Tracking:'.
    for carrier,lengths in [('FedEx',(12,15,20,22)),('DHL',(10,))]:
        for match in re.finditer(carrier+r'[^\n]{0,35}?\b(\d{10,22})\b',text,re.I):
            if len(match.group(1)) in lengths:numbers.append((carrier,match.group(1)))
    if strict:
        # Require both a recognizable tracking identifier and a specific shipping update.
        promotional=re.search(r'\b(free shipping|free delivery|sale|coupon|promo code|percent off|% off|shop now|limited.time offer|win a|you.ve won)\b',subject,re.I)
        if not numbers or status=='Shipping notice' or promotional:return []
    eta = '' 
    for line in text.splitlines():
        if re.search(r'(estimated delivery|expected delivery|arriv(?:ing|es)|deliver(?:y|ed) by)',line,re.I):
            eta = ' '.join(line.split())[:160]; break
    try:
        sent = parsedate_to_datetime(str(message.get('Date','')))
        if sent.tzinfo is None: sent=sent.replace(tzinfo=timezone.utc)
    except Exception:
        sent = datetime.now(timezone.utc)
    if not numbers:
        # Keep unrecognized notices separate; never claim these are confirmed packages.
        identity = str(message.get('Message-ID','')) or subject+sender+str(sent)
        numbers = [('Unmatched notice',hashlib.sha256(identity.encode()).hexdigest()[:16])]
    output=[]
    for carrier,number in dict.fromkeys(numbers):
        link = {'UPS':'https://www.ups.com/track?tracknum=',
                'USPS':'https://tools.usps.com/go/TrackConfirmAction?tLabels=',
                'FedEx':'https://www.fedex.com/fedextrack/?trknbr=',
                'DHL':'https://www.dhl.com/global-en/home/tracking.html?tracking-id='}.get(carrier,'')
        output.append(dict(id=carrier+':'+number,carrier=carrier,number=number,
            title=subject or 'Shipment notice',sender=sender,status=status,eta=eta,
            date=sent,link=link+quote(number) if link else ''))
    return output

def fetch_shipments(config,password):
    if not config['email_enabled']: return [],None
    if not password: return [],'Enter an email app password in Settings, or set MIRROR_EMAIL_PASSWORD.'
    client=None
    try:
        client=imaplib.IMAP4_SSL(config['email_host'],993,ssl_context=ssl.create_default_context(),timeout=8)
        client.login(config['email_user'],password)
        status,_=client.select('"'+config['email_folder'].replace('\\','\\\\').replace('"','\\"')+'"',readonly=True)
        if status != 'OK': return [],'Cannot open email folder; check its name.'
        since=(datetime.now()-timedelta(days=config['email_days'])).strftime('%d-%b-%Y')
        status,data=client.uid('search',None,'SINCE',since)
        if status != 'OK': return [],'Email search failed.'
        # Search shipping-related subjects before applying the scan limit, so
        # newsletters and ordinary mail cannot crowd older shipments out.
        all_ids=data[0].split()
        terms=['shipped','shipment','tracking','delivery','delivered','package','parcel','on its way','on the way','dispatched']
        expression='SUBJECT "'+terms[-1]+'"'
        for term in reversed(terms[:-1]):expression='OR SUBJECT "'+term+'" ('+expression+')'
        candidate_status,candidate_data=client.uid('search',None,'SINCE',since,'('+expression+')')
        candidates=candidate_data[0].split() if candidate_status=='OK' and candidate_data and isinstance(candidate_data[0],bytes) else []
        selected=candidates or all_ids
        identifiers=selected[-config['email_limit']:]
        deadline=monotonic()+25
        newest={}
        for uid in reversed(identifiers):
            if monotonic()>deadline:break
            # Fetch a bounded prefix, read-only, so messages are not marked read.
            status,data=client.uid('fetch',uid,'(BODY.PEEK[]<0.262144>)')
            if status != 'OK': continue
            raw=next((item[1] for item in data if isinstance(item,tuple)),None)
            if not raw: continue
            try:notices=parse_shipment(raw,strict=config.get('email_strict',True),blocked=config.get('email_blocked',''))
            except Exception:continue
            for notice in notices:
                previous=newest.get(notice['id'])
                if previous is None or notice['date'] > previous['date']:
                    newest[notice['id']]=notice
        return sorted(newest.values(),key=lambda n:n['date'],reverse=True),None
    except imaplib.IMAP4.error:
        return [],'Email sign-in failed. Check IMAP access and your app password.'
    except Exception:
        return [],'Email connection failed. Check server, network and account settings.'
    finally:
        if client is not None:
            try: client.logout()
            except Exception: pass

WEATHER_CODES = {0:'Clear sky',1:'Mostly clear',2:'Partly cloudy',3:'Overcast',45:'Fog',48:'Freezing fog',
    51:'Light drizzle',53:'Drizzle',55:'Heavy drizzle',56:'Freezing drizzle',57:'Freezing drizzle',
    61:'Light rain',63:'Rain',65:'Heavy rain',66:'Freezing rain',67:'Freezing rain',71:'Light snow',
    73:'Snow',75:'Heavy snow',77:'Snow grains',80:'Rain showers',81:'Rain showers',82:'Heavy showers',
    85:'Snow showers',86:'Heavy snow showers',95:'Thunderstorm',96:'Thunderstorm with hail',99:'Thunderstorm with hail'}

def fetch_weather(config):
    if not config['zip_code']: return None,None
    try:
        lookup=requests.get('https://api.zippopotam.us/us/'+config['zip_code'],timeout=(8,15))
        lookup.raise_for_status()
        place=lookup.json()['places'][0]
        params=dict(latitude=place['latitude'],longitude=place['longitude'],
            current='temperature_2m,apparent_temperature,relative_humidity_2m,weather_code,wind_speed_10m',
            daily='temperature_2m_max,temperature_2m_min,sunrise,sunset',timezone='auto',forecast_days=2,
            temperature_unit=config['units'],wind_speed_unit='mph' if config['units']=='fahrenheit' else 'kmh')
        response=requests.get('https://api.open-meteo.com/v1/forecast',params=params,timeout=(8,20))
        response.raise_for_status()
        data=response.json()
        for key in ['temperature_2m','apparent_temperature','relative_humidity_2m','weather_code','wind_speed_10m']:
            float(data['current'][key])
        for key in ['temperature_2m_max','temperature_2m_min']:
            float(data['daily'][key][0])
        for key in ['sunrise','sunset']:
            if data['daily'][key][0]: datetime.fromisoformat(data['daily'][key][0])
        str(data['current_units']['wind_speed_10m'])
        str(data['current']['time'])
        ZoneInfo(data['timezone'])
        data['latitude']=float(place['latitude'])
        data['longitude']=float(place['longitude'])
        data['place']=place['place name']+', '+place['state abbreviation']
        return data,None
    except requests.HTTPError as error:
        return None,('ZIP code not found.' if error.response.status_code==404 else 'Weather service unavailable.')
    except Exception:
        return None,'Weather unavailable. Check internet and ZIP code.'


from datetime import time
from icalendar import Calendar
import recurring_ical_events
def as_datetime(value, zone):
    if isinstance(value, datetime):
        return value.replace(tzinfo=zone) if value.tzinfo is None else value.astimezone(zone)
    return datetime.combine(value, time.min, zone)

def parse_events(raw, source, now, days):
    """Expand recurrence including overrides/exclusions; end dates are exclusive."""
    zone = now.tzinfo
    calendar = Calendar.from_ical(raw)
    stop = datetime.combine(now.date() + timedelta(days=days+1), time.min, zone)
    result = []
    recurring_uids = {str(e.get('UID','')) for e in calendar.walk('VEVENT') if e.get('RRULE') or e.get('RDATE') or e.get('RECURRENCE-ID')}
    past=max(14 if source.get('assignments') else 0,source.get('schedule_past_days',0))
    begin=(now-timedelta(days=past)).replace(hour=0,minute=0,second=0,microsecond=0) if past else now
    for event in recurring_ical_events.of(calendar).between(begin, stop):
        if str(event.get('STATUS', '')).upper() == 'CANCELLED':
            continue
        start_value = event.decoded('DTSTART')
        all_day = not isinstance(start_value, datetime)
        start = as_datetime(start_value, zone)
        end_value = event.decoded('DTEND', None)
        end = as_datetime(end_value, zone) if end_value is not None else start + event.decoded('DURATION', timedelta(days=1) if all_day else timedelta())
        if end <= now and start < now and not past:
            continue
        identity = str(event.get('UID','')) or str(event.get('SUMMARY',''))+start.isoformat()
        occurrence = str(event.get('RECURRENCE-ID','')) if identity in recurring_uids else ''
        key = hashlib.sha256((source['url']+'|'+identity+'|'+occurrence).encode()).hexdigest()
        result.append(dict(key=key, assignment=source.get('assignments',False), title=str(event.get('SUMMARY', '(Untitled)')),
                           location=str(event.get('LOCATION', '')), start=start,
                           end=end, all_day=all_day, source=source['name'], color=source['color']))
    return result

def fetch_calendar(source, now, days):
    try:
        headers={'Accept':'text/calendar, application/ics;q=0.9, */*;q=0.1'}
        options={}
        if source.get('auth_type')=='basic':options['auth']=(source.get('auth_user',''),source.get('auth_password',''))
        elif source.get('auth_type')=='bearer':headers['Authorization']='Bearer '+source.get('auth_token','')
        with requests.get(source['url'], headers=headers, timeout=(8, 20), stream=True, **options) as response:
            response.raise_for_status()
            content = bytearray()
            for chunk in response.iter_content(65536):
                content.extend(chunk)
                if len(content) > 10_000_000:
                    raise ValueError('Feed too large')
        return parse_events(bytes(content), source, now, days), None
    except requests.HTTPError as error:
        code=error.response.status_code
        return [], ('Calendar access denied (HTTP '+str(code)+'). Check the secret iCal URL or authentication settings.' if code in (401,403) else f'HTTP {code}; check calendar link')
    except requests.RequestException:
        return [], 'Connection failed; check internet or calendar link'
    except Exception:
        return [], 'Unable to read iCal data. Use a subscription/feed URL, not a browser login or calendar sharing page.'


#!/usr/bin/env python3
"""Personal Operations: local Python dashboard and authenticated phone controller."""
import argparse
import copy
import hashlib
import hmac
import ipaddress
import json
import mimetypes
import os
from pathlib import Path
import re
import secrets
import socket
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse
from zoneinfo import ZoneInfo
import webbrowser
from portable import export_csv, parse_csv
from aerospace import fetch_news, daily_trivia
from idrac import fetch_idrac, restore_automatic
import requests
from services import fetch_calendar, fetch_weather, fetch_shipments, WEATHER_CODES

ROOT=Path(__file__).resolve().parent
THEMES=['aurora', 'nebula', 'amber', 'ocean', 'solar', 'lunar', 'forest', 'retro']+['lcars','red-alert','mission-control','expanse','minimal','blueprint','warm-night']
PAGES=['daily','school','workshop','calendar']
WIDGETS=['yearprogress','daylight','mission','schoolcommute','commute','clock','upnext','weather','agenda','assignments','shipments','countdowns','notes','radar','workshop','connections','classes','sensors']
DEFAULT=dict(version=29,fan_control_enabled=False,fan_min_percent=20,fan_target_c=46,fan_gain=2.5,fan_failsafe_c=75,idrac_enabled=False,idrac_host='',idrac_user='',idrac_password='',theme='lcars',timezone='America/Chicago',hour24=False,seconds=False,days=14,refresh=5,
    layout_revision=2,layout_theme='lcars',thursday_alert=True,font_base=18,tv_mode=True,routes_enabled=False,routes_key='',school_origin='',school_destination='',commute_origin='',commute_destination='',zip_code='',units='fahrenheit',notes='Make room for a good day.',calendars=[],completed={},
    schedule_past_days=0,schedule_future_days=14,schedule_all_day=True,schedule_locations=True,assume_delivered_days=0,email_accounts=[],email_strict=True,email_blocked='',email_enabled=False,email_host='imap.gmail.com',email_user='',email_folder='INBOX',email_days=30,email_limit=100,
    auto_night=True,night_mode='sun',night_start='21:00',night_end='07:00',day_brightness=100,night_brightness=55,
    urgent_red=False,shift_pixels=True,blank_minutes=0,blank_seconds=10,hide_delivered_days=3,
    page='daily',preset='landscape',layouts={},hidden={},rotation_seconds=0,
    countdowns=[],classes=[],workshop=[],manual_shipments=[],sensors=[],sensor_file='')
COLLECTIONS={'countdowns','classes','workshop','manual_shipments'}

def stamp():return datetime.now(timezone.utc).isoformat()
def encode(value):
    if isinstance(value,datetime):return value.isoformat()
    raise TypeError(type(value).__name__)
def safe_url(value):
    parsed=urlparse(value)
    return parsed.scheme=='https' and bool(parsed.hostname) and not parsed.username and not parsed.password

def validate(config):
    for key in ['commute_origin','commute_destination','school_origin','school_destination','routes_key']:
        if not isinstance(config[key],str) or len(config[key])>500:raise ValueError('Use an address shorter than 500 characters.')
    if config['fan_control_enabled'] and not config['idrac_enabled']:raise ValueError('Enable iDRAC monitoring before fan control.')
    if not 10<=float(config['fan_min_percent'])<=100 or not 20<=float(config['fan_target_c'])<=65 or not 0.5<=float(config['fan_gain'])<=10 or not 50<=float(config['fan_failsafe_c'])<=90 or float(config['fan_failsafe_c'])<=float(config['fan_target_c']):raise ValueError('Invalid fan-control temperature or speed settings.')
    if config['idrac_enabled']:
        try:ipaddress.ip_address(config['idrac_host'])
        except ValueError:raise ValueError('Enter a valid iDRAC IP address.')
        if not config['idrac_user'] or not config['idrac_password']:raise ValueError('Enter the iDRAC username and password.')
    for key in ['idrac_host','idrac_user','idrac_password']:
        if not isinstance(config[key],str) or len(config[key])>255 or any(c in config[key] for c in '\r\n'):raise ValueError('Invalid iDRAC setting.')
    if config['theme'] not in THEMES or config['page'] not in PAGES:raise ValueError('Unknown theme or page.')
    if config['preset'] not in ['landscape','portrait','night']:raise ValueError('Unknown layout preset.')
    ZoneInfo(config['timezone'])
    for key,low,high in [('assume_delivered_days',0,365),('font_base',10,40),('schedule_past_days',0,90),('schedule_future_days',0,90),('days',1,90),('refresh',1,60),('email_days',1,90),('email_limit',10,500),('day_brightness',20,100),('night_brightness',10,100),('blank_minutes',0,240),('blank_seconds',1,60),('hide_delivered_days',0,90),('rotation_seconds',0,3600)]:
        config[key]=int(config[key])
        if not low<=config[key]<=high:raise ValueError(f'{key}: use {low}–{high}.')
    if config['zip_code'] and not re.fullmatch(r'\d{5}',config['zip_code']):raise ValueError('ZIP must contain five digits.')
    if config['units'] not in ['fahrenheit','celsius']:raise ValueError('Invalid temperature unit.')
    for key in ['night_start','night_end']:
        datetime.strptime(config[key],'%H:%M')
    if config['night_mode'] not in ['sun','schedule']:raise ValueError('Invalid night mode.')
    for key in ['fan_control_enabled','idrac_enabled','thursday_alert','tv_mode','routes_enabled','schedule_all_day','schedule_locations','hour24','seconds','email_enabled','auto_night','urgent_red','shift_pixels']:
        if type(config[key]) is not bool:raise ValueError(f'{key} must be true or false.')
    if config['email_enabled'] and (not re.fullmatch(r'[\w.-]+',config['email_host']) or not config['email_user'] or '\n' in config['email_folder'] or '\r' in config['email_folder']):raise ValueError('Check the email server, username and folder.')
    if type(config['email_strict']) is not bool or not isinstance(config['email_blocked'],str):raise ValueError('Invalid shipment filters.')
    accounts=config['email_accounts']
    if not isinstance(accounts,list) or len(accounts)>20:raise ValueError('Use up to 20 additional email accounts.')
    ids=set()
    for a in accounts:
        if not isinstance(a,dict) or any(not isinstance(a.get(k),str) for k in ['id','name','host','user','folder','password']):raise ValueError('Invalid email account.')
        if not a['id'] or a['id'] in ids:raise ValueError('Duplicate email account.')
        ids.add(a['id'])
        if not a['name'] or not re.fullmatch(r'[\w.-]+',a['host']) or not a['user'] or not a['folder'] or any(c in a['folder'] for c in '\r\n') or type(a.get('enabled')) is not bool:raise ValueError('Check account name, server, username and folder.')
    if len(config['notes'])>4000:raise ValueError('Notes are limited to 4,000 characters.')
    for cal in config['calendars']:
        if isinstance(cal.get('url'),str) and cal['url'].lower().startswith('webcal://'):cal['url']='https://'+cal['url'][9:]
        if cal.get('auth_type','none') not in ['none','basic','bearer']:raise ValueError('Invalid calendar authentication mode.')
        for key in ['auth_user','auth_password','auth_token']:
            if not isinstance(cal.get(key,''),str) or any(c in cal.get(key,'') for c in '\r\n'):raise ValueError('Invalid calendar credential.')
        if cal.get('auth_type')=='basic' and not cal.get('auth_user'):raise ValueError('Enter the private calendar username.')
        if cal.get('auth_type')=='bearer' and not cal.get('auth_token'):raise ValueError('Enter the private calendar token.')
        if type(cal.get('class_times',False)) is not bool:raise ValueError('Class Times selection must be true or false.')
        if type(cal.get('show_schedule',True)) is not bool:raise ValueError('Schedule visibility must be true or false.')
        if not cal.get('name') or not safe_url(cal.get('url','')):raise ValueError('Calendars need a name and HTTPS iCal URL.')
        if not re.fullmatch(r'#[0-9A-Fa-f]{6}',cal.get('color','')):raise ValueError('Invalid calendar color.')
    for page,layout in config['layouts'].items():
        if page not in PAGES:raise ValueError('Unknown layout page.')
        for key,item in layout.items():
            if key not in WIDGETS:raise ValueError('Unknown widget.')
            if not isinstance(item,dict):raise ValueError('Invalid widget layout.')
            for axis,low,high in [('x',0,100),('y',0,3000),('w',16,100),('h',100,1600)]:
                val=item.get(axis)
                if not isinstance(val,(int,float)) or not low<=val<=high:raise ValueError(f'Invalid widget bounds for {key}: {axis} must be {low}–{high}.')
            if item['x']+item['w']>100.1:raise ValueError('Widget extends beyond the display.')
    for page,hidden in config['hidden'].items():
        if page not in PAGES or not isinstance(hidden,list) or any(k not in WIDGETS for k in hidden):raise ValueError('Invalid hidden widgets.')
    for collection in COLLECTIONS:
        if len(config[collection])>500:raise ValueError('Too many saved items.')
        for item in config[collection]:
            if not item.get('title') or len(item['title'])>300:raise ValueError('Each item needs a title (up to 300 characters).')
            if collection=='countdowns':datetime.fromisoformat(item['target'])
            if collection=='classes':
                datetime.strptime(item['time'],'%H:%M');datetime.strptime(item['end'],'%H:%M')
                if not item.get('days') or any(d not in range(7) for d in item['days']):raise ValueError('Choose class weekdays.')
            if collection=='workshop' and item.get('due'):datetime.fromisoformat(item['due'])
            if collection=='manual_shipments' and item.get('stage') not in ['Ordered','Shipped','Out for delivery','Delivered']:raise ValueError('Invalid shipment stage.')
    return config

def assignment_summary(events,completed,now):
    rows=[]
    for event in events:
        if not event.get('assignment'):continue
        start=datetime.fromisoformat(event['start']).astimezone(now.tzinfo)
        done=bool(completed.get(event['key']))
        overdue=(start.date()<now.date() if event['all_day'] else start<now) and not done
        category='completed' if done else 'overdue' if overdue else 'today' if start.date()==now.date() else 'week' if start.date()<=now.date()+timedelta(days=7) else 'later'
        rows.append({**event,'done':done,'priority':category})
    return rows

def schedule_events(classes,now,past=0,future=7):
    result=[]
    for item in classes:
        for offset in range(-past,future+1):
            day=now.date()+timedelta(days=offset)
            if day.weekday() not in item['days']:continue
            start=datetime.combine(day,datetime.strptime(item['time'],'%H:%M').time(),now.tzinfo)
            end=datetime.combine(day,datetime.strptime(item['end'],'%H:%M').time(),now.tzinfo)
            if end<=start:end+=timedelta(days=1)
            if end<now and not past:continue
            result.append(dict(key='class:'+item['id']+str(day),title=item['title'],start=start.isoformat(),end=end.isoformat(),location=' • '.join(filter(None,[item.get('building'),item.get('room')])),source='Class timetable',color='#9cafff',all_day=False,assignment=False))
    return result

def effective_display(config,weather,alerts,assignments,now):
    night=False;reason='Manual theme'
    if config['auto_night']:
        current=now.strftime('%H:%M');start,end=config['night_start'],config['night_end']
        night=(current>=start or current<end) if start>end else start<=current<end
        reason='Night schedule' if night else 'Day schedule'
        try:
            local=now.astimezone(ZoneInfo(weather['timezone']))
            sunrise=datetime.fromisoformat(weather['daily']['sunrise'][0]).replace(tzinfo=local.tzinfo)
            sunset=datetime.fromisoformat(weather['daily']['sunset'][0]).replace(tzinfo=local.tzinfo)
            if config['night_mode']=='sun' and sunrise.date()==local.date():
                night=local<sunrise or local>=sunset
                reason='After sunset / before sunrise' if night else 'Daylight at ZIP location'
        except (KeyError,TypeError,ValueError):pass
    urgent=any(a.get('severity') in ['Extreme','Severe'] for a in alerts)
    urgent=urgent or any(not a['done'] and a['priority']=='overdue' and datetime.fromisoformat(a['start']).astimezone(now.tzinfo).date()==now.date() for a in assignments)
    weekend=[]
    if config.get('thursday_alert',True) and now.weekday()==3:
        friday=now.date()+timedelta(days=1);sunday=friday+timedelta(days=2)
        weekend=[a for a in assignments if not a.get('done') and friday<=datetime.fromisoformat(a['start']).astimezone(now.tzinfo).date()<=sunday]
    theme='red-alert' if weekend else 'red-alert' if config['urgent_red'] and urgent else 'warm-night' if night else config['theme']
    return dict(weekend_count=len(weekend),weekend_day=now.date().isoformat(),theme=theme,night=night,brightness=config['night_brightness'] if night else config['day_brightness'],reason='Thursday weekend assignment alert' if weekend else 'Urgent reminder / alert' if theme=='red-alert' and config['urgent_red'] and urgent else reason)

def local_ip():
    try:
        with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as connection:
            connection.connect(('8.8.8.8',80));return connection.getsockname()[0]
    except OSError:
        try:
            addresses=socket.gethostbyname_ex(socket.gethostname())[2]
            return next((a for a in addresses if not a.startswith('127.')),'Unavailable')
        except OSError:return 'Unavailable'

class Store:
    def __init__(self,directory,demo=False):
        self.directory=Path(directory);self.file=self.directory/'settings.csv';self.lock=threading.RLock()
        self.config=copy.deepcopy(DEFAULT);self.demo=demo;self.generation=0;self.busy=False
        self.password=os.environ.get('MIRROR_EMAIL_PASSWORD','');self.data={};self.connections={};self.error_log=[]
        self.token=secrets.token_urlsafe(6);self.local_ip=local_ip()
        legacy=self.directory/'settings.json'
        if self.file.exists():
            old,password=parse_csv(self.file.read_text(encoding='utf-8-sig'))
            self.config=self.normalized_config(old)
            self.password=os.environ.get('MIRROR_EMAIL_PASSWORD',password)
        elif legacy.exists():
            self.config=self.normalized_config(json.loads(legacy.read_text()))
        validate(self.config)
        if demo:self.load_demo()
        elif not self.file.exists():self.save()
        self.news_day=None
        self.news_cache=self.directory/'aerospace_news.json'
        if not demo and self.news_cache.exists():
            try:
                cache=json.loads(self.news_cache.read_text())
                self.data['news']=cache['items'];self.news_day=cache['day']
            except (OSError,ValueError,KeyError):pass

    def normalized_config(self,values):
        config=copy.deepcopy(DEFAULT)
        for key,value in values.items():
            if key in DEFAULT and key not in ['version','sensors']:
                default=DEFAULT[key]
                if type(value) is not type(default):raise ValueError('Invalid type for setting: '+key)
                config[key]=value
        if values.get('layout_revision',0)<2:
            config['layouts'].pop('daily',None)
            config['hidden']['daily']=['radar','workshop','connections','classes','sensors','yearprogress','mission','schoolcommute','daylight']
        for cal in config['calendars']:cal.setdefault('id',secrets.token_hex(8))
        if config['theme']=='mirror':config['theme']='minimal'
        return validate(config)

    def write_private(self,path,text):
        self.directory.mkdir(parents=True,exist_ok=True)
        temporary=path.with_suffix(path.suffix+'.tmp')
        fd=os.open(temporary,os.O_WRONLY|os.O_CREAT|os.O_TRUNC,0o600)
        with os.fdopen(fd,'w',encoding='utf-8',newline='') as stream:stream.write(text)
        os.replace(temporary,path)

    def save(self):
        self.write_private(self.file,export_csv(self.config,self.password))

    def backup(self):
        with self.lock:return export_csv(self.config,self.password)

    def import_backup(self,text):
        settings,password=parse_csv(text)
        new=self.normalized_config(settings)
        with self.lock:
            # Retain the previous state so an accidental import can be undone.
            self.write_private(self.directory/'settings.before-import.csv',self.backup())
            previous,previous_password=self.config,self.password
            self.config,self.password=new,password
            try:self.save()
            except Exception:self.config,self.password=previous,previous_password;raise
            self.generation+=1
            self.data={k:v for k,v in self.data.items() if k=='news'};self.connections={}

    def public_config(self):
        config=copy.deepcopy(self.config)
        config['calendars']=[{k:v for k,v in cal.items() if k not in ['url','auth_password','auth_token']} for cal in config['calendars']]
        config.pop('routes_key',None)
        config.pop('idrac_password',None)
        config['email_password_saved']=bool(self.password)
        config['email_accounts']=[{**{k:v for k,v in a.items() if k!='password'},'password_saved':bool(a['password'])} for a in config['email_accounts']]
        config['sensor_file_configured']=bool(config.pop('sensor_file'))
        return config

    def state(self):
        with self.lock:
            now=datetime.now(ZoneInfo(self.config['timezone']))
            events=[e for key,value in self.data.items() if key.startswith('calendar:') for e in value]
            events+=schedule_events(self.config['classes'],now)
            newly_completed=[]
            for event in events:
                if not event.get('assignment') or self.config['completed'].get(event['key']):continue
                due=datetime.fromisoformat(event['start']) if isinstance(event['start'],str) else event['start']
                due=due.astimezone(now.tzinfo)
                expired=(now.date()-due.date()).days>7 if event['all_day'] else now-due>timedelta(days=7)
                if expired:newly_completed.append(event['key'])
            if newly_completed:
                previous=copy.deepcopy(self.config['completed'])
                self.config['completed'].update(dict.fromkeys(newly_completed,True))
                try:self.save()
                except Exception:self.config['completed']=previous;raise
            def visible(event):return not (event.get('assignment') and self.config['completed'].get(event['key']))
            events=[e for e in events if visible(e)]
            class_ids={'calendar:'+c['id'] for c in self.config['calendars'] if c.get('enabled',True) and c.get('class_times',False)}
            class_events=[e for key,rows in self.data.items() if key in class_ids for e in rows if datetime.fromisoformat(e['end'])>=now]
            class_events.sort(key=lambda e:datetime.fromisoformat(e['start']))
            visible_ids={'calendar:'+c['id'] for c in self.config['calendars'] if c.get('enabled',True) and c.get('show_schedule',True)}
            agenda=[e for key,rows in self.data.items() if key in visible_ids for e in rows]
            agenda+=schedule_events(self.config['classes'],now,self.config['schedule_past_days'],self.config['schedule_future_days'])
            lower=(now-timedelta(days=self.config['schedule_past_days'])).replace(hour=0,minute=0,second=0,microsecond=0) if self.config['schedule_past_days'] else now
            upper=(now+timedelta(days=self.config['schedule_future_days']+1)).replace(hour=0,minute=0,second=0,microsecond=0)
            def dt(value):return datetime.fromisoformat(value) if isinstance(value,str) else value
            agenda=sorted([e for e in agenda if visible(e) and dt(e['end'])>=lower and dt(e['start'])<upper],key=lambda e:dt(e['start']))
            events.sort(key=lambda e:dt(e['start']))
            assignment_stop=(now+timedelta(days=self.config['days']+1)).replace(hour=0,minute=0,second=0,microsecond=0)
            assignments=assignment_summary([e for e in events if now-timedelta(days=14)<=dt(e['start'])<assignment_stop],self.config['completed'],now)
            alerts=[a for a in self.data.get('alerts',[]) if not a.get('expires') or datetime.fromisoformat(a['expires'])>now]
            weather=self.data.get('weather')
            shipments=copy.deepcopy(self.data.get('email',[]))
            for key,rows in self.data.items():
                if key.startswith('email:'):shipments.extend(copy.deepcopy(rows))
            unique={}
            for row in shipments:
                if row['id'] not in unique or row['date']>unique[row['id']]['date']:unique[row['id']]=row
            shipments=list(unique.values())
            shipments=[s for s in shipments if datetime.fromisoformat(s['date'])>=now-timedelta(days=self.config['email_days'])]
            for shipment in shipments:
                status=shipment['status']
                shipment['stage']='Delivered' if status=='Delivered' else 'Out for delivery' if status=='Out for delivery' else 'Shipped'
                threshold=self.config['assume_delivered_days']
                if threshold and status!='Delivered' and now-datetime.fromisoformat(shipment['date'])>timedelta(days=threshold):
                    shipment['stage']='Delivered';shipment['assumed_delivered']=True
                    shipment['updated']=(datetime.fromisoformat(shipment['date'])+timedelta(days=threshold)).isoformat()

            shipments+=copy.deepcopy(self.config['manual_shipments'])
            cutoff=now-timedelta(days=self.config['hide_delivered_days'])
            shipments=[s for s in shipments if s.get('stage')!='Delivered' or datetime.fromisoformat(s.get('updated',s.get('date',stamp())))>=cutoff]
            for key,connection in self.connections.items():
                connection['stale']=bool(connection.get('success') and (now-datetime.fromisoformat(connection['success'])).total_seconds()>(129600 if key=='news' else max(self.config['refresh']*180,900)))
            return dict(config=self.public_config(),now=now.isoformat(),demo=self.demo,busy=self.busy,events=events,schedule_events=agenda,assignments=assignments,
                weather=weather,alerts=alerts,radar=self.data.get('radar'),shipments=shipments,
                trivia=daily_trivia(self.data.get('news',[]),now),
                idrac=copy.deepcopy(self.data.get('idrac')),local_ip=self.local_ip,class_events=class_events,commutes=copy.deepcopy(self.data.get('commutes',{})),error_log=copy.deepcopy(self.error_log),sensors=self.data.get('sensors',[]),connections=copy.deepcopy(self.connections),
                display=effective_display(self.config,weather,alerts,assignment_summary(events,self.config['completed'],now),now))

    def mutate(self,body):
        with self.lock:
            action=body.get('action');new=copy.deepcopy(self.config)
            if action=='import_csv':
                self.import_backup(body.get('csv',''));return
            if action=='settings':
                allowed=set(DEFAULT)-{'version','email_accounts','calendars','completed','countdowns','classes','workshop','manual_shipments','sensors','layouts','hidden'}
                values=body.get('values',{})
                if set(values)-allowed-{'email_password','clear_email_password','clear_idrac_password'}:raise ValueError('Unknown setting.')
                for key,value in values.items():
                    if key in allowed:new[key]=value
                if values.get('clear_idrac_password'):new['idrac_password']=''
                if 'theme' in values and values['theme']!=self.config['theme']:
                    new['auto_night']=False;new['urgent_red']=False
            elif action=='email_account':
                item=body['item'];existing=next((a for a in new['email_accounts'] if a['id']==item.get('id')),None)
                if item.get('id') and not existing:raise ValueError('Email account not found.')
                if body.get('delete'):
                    new['email_accounts']=[a for a in new['email_accounts'] if a['id']!=item.get('id')]
                else:
                    account={k:item.get(k,(existing or {}).get(k,'')) for k in ['name','host','user','folder']}
                    account.update(id=existing['id'] if existing else secrets.token_hex(8),enabled=item.get('enabled',True),password=item.get('password') or (existing or {}).get('password',''))
                    if item.get('clear_password'):account['password']=''
                    new['email_accounts']=[a for a in new['email_accounts'] if a['id']!=account['id']]+[account]
            elif action=='calendar':
                item=body['item'];existing=next((c for c in new['calendars'] if c['id']==item.get('id')),None)
                if body.get('delete'):
                    new['calendars']=[c for c in new['calendars'] if c['id']!=item.get('id')]
                else:
                    source={**(existing or {}),**item};source['id']=existing['id'] if existing else secrets.token_hex(8)
                    if not item.get('url') and existing:source['url']=existing['url']
                    source.setdefault('enabled',True);source.setdefault('assignments',False)
                    new['calendars']=[c for c in new['calendars'] if c['id']!=source['id']]+[source]
            elif action=='complete':
                if not isinstance(body.get('key'),str) or not isinstance(body.get('done'),bool):raise ValueError('Invalid checklist change.')
                new['completed'][body['key']]=body['done']
            elif action=='item':
                collection=body['collection']
                if collection not in COLLECTIONS:raise ValueError('Unknown collection.')
                item=copy.deepcopy(body['item']);item['id']=item.get('id') or secrets.token_hex(8)
                item['updated']=stamp()
                if collection=='countdowns' and not body.get('delete'):
                    target=datetime.fromisoformat(item['target'])
                    if target.tzinfo is None:target=target.replace(tzinfo=ZoneInfo(new['timezone']))
                    item['target']=target.isoformat()
                if collection=='workshop' and item.get('due') and len(item['due'])==10:
                    item['due']=datetime.fromisoformat(item['due']+'T12:00:00').replace(tzinfo=ZoneInfo(new['timezone'])).isoformat()
                new[collection]=[x for x in new[collection] if x['id']!=item['id']]
                if not body.get('delete'):new[collection].append(item)
            elif action=='layout':
                page=body['page']
                if page not in PAGES:raise ValueError('Invalid page.')
                new['layout_theme']='lcars' if new['theme'] in ['lcars','red-alert'] else new['theme']
                new['layouts'][page]=body.get('layout',{})
                new['hidden'][page]=body.get('hidden',[])
            elif action=='preset':
                new['preset']=body['preset'];new['layouts']={};new['hidden']={}
            elif action=='sensors':
                rows=body.get('values',[])
                if not isinstance(rows,list) or len(rows)>20:raise ValueError('Use up to 20 sensor readings.')
                for row in rows:
                    if not isinstance(row.get('name'),str) or not isinstance(row.get('value'),(int,float,str)) or len(str(row.get('value')))>60:raise ValueError('Invalid sensor reading.')
                self.data['sensors']=[{**r,'updated':stamp()} for r in rows]
                return
            else:raise ValueError('Unknown action.')
            validate(new)
            old,old_password=self.config,self.password;self.config=new
            if action=='settings':
                if body['values'].get('clear_email_password'):self.password=''
                elif body['values'].get('email_password'):self.password=body['values']['email_password']
            try:self.save()
            except Exception:self.config,self.password=old,old_password;raise
            if action in ['settings','calendar','email_account']:
                self.generation+=1
                if action=='settings':
                    changed=body['values']
                    if any(k.startswith('idrac_') for k in changed):self.data.pop('idrac',None);self.connections.pop('idrac',None)
                    if any(k in changed for k in ['zip_code','units']):
                        for key in ['weather','alerts','radar']:self.data.pop(key,None);self.connections.pop(key,None)
                    if any(k.startswith('email_') for k in changed):self.data.pop('email',None);self.connections.pop('email',None)
                if action=='email_account' or (action=='settings' and any(k.startswith('email_') for k in body['values'])):
                    for key in list(self.data):
                        if key.startswith('email:'):self.data.pop(key,None);self.connections.pop(key,None)
                allowed_ids={'calendar:'+c['id'] for c in new['calendars'] if c.get('enabled',True)}
                for key in list(self.data):
                    if key.startswith('calendar:') and key not in allowed_ids:self.data.pop(key,None);self.connections.pop(key,None)

    def log_error(self,source,message):
        with self.lock:
            text=str(message)
            secrets_to_hide=[self.password,self.token,self.config['routes_key'],self.config['idrac_password']]+[a['password'] for a in self.config['email_accounts']]+[c.get(k,'') for c in self.config['calendars'] for k in ['url','auth_password','auth_token']]
            for secret in secrets_to_hide:
                if secret:text=text.replace(secret,'[private]')
            text=re.sub(r'https?://\S+','[URL]',text)[:400]
            if self.error_log and self.error_log[-1]['source']==source and self.error_log[-1]['message']==text:return
            self.error_log.append(dict(time=stamp(),source=source,message=text))
            self.error_log=self.error_log[-30:]

    def record(self,key,label,result):
        data,error=result
        if error and self.connections.get(key,{}).get('error')!=error:self.log_error(label,error)
        self.connections[key]=dict(label=label,attempt=stamp(),success=self.connections.get(key,{}).get('success'),error=error)
        if not error:
            if key=='email' or key.startswith('email:'):
                merged={n['id']:n for n in self.data.get(key,[])}
                for notice in json.loads(json.dumps(data,default=encode)):
                    if notice['id'] not in merged or notice['date']>=merged[notice['id']]['date']:merged[notice['id']]=notice
                data=sorted(merged.values(),key=lambda n:n['date'],reverse=True)[:500]
            self.data[key]=json.loads(json.dumps(data,default=encode));self.connections[key]['success']=stamp()

    def refresh(self):
        with self.lock:
            if self.busy or self.demo:return
            self.busy=True;config=copy.deepcopy(self.config);generation=self.generation;password=self.password
        def work():
            try:
                jobs=[];now=datetime.now(ZoneInfo(config['timezone']))
                with ThreadPoolExecutor(max_workers=4) as pool:

                    if self.news_day!=now.date().isoformat():jobs.append(('news','Daily aerospace trivia',pool.submit(fetch_news)))
                    if config['routes_enabled'] and config['routes_key']:
                        jobs.append(('commutes','Google Routes',pool.submit(fetch_commutes,config)))
                    for source in config['calendars']:
                        if source.get('enabled',True):jobs.append(('calendar:'+source['id'],source['name'],pool.submit(fetch_calendar,{**source,'schedule_past_days':config['schedule_past_days']},now,max(7 if config['thursday_alert'] else 0,config['days'],config['schedule_future_days']))))
                    if config['zip_code']:jobs.append(('weather','Weather',pool.submit(fetch_weather,config)))
                    if config['email_enabled']:jobs.append(('email','Shipment email',pool.submit(fetch_shipments,config,password)))
                    for account in config['email_accounts']:
                        if account['enabled']:
                            options={**config,'email_enabled':True,**{'email_'+k:account[k] for k in ['host','user','folder']}}
                            jobs.append(('email:'+account['id'],account['name'],pool.submit(fetch_shipments,options,account['password'])))
                    lookup={future:(key,label) for key,label,future in jobs}
                    for future in as_completed(lookup):
                        key,label=lookup[future]
                        try:result=future.result()
                        except Exception:result=(None,'Connection failed; retry later.')
                        with self.lock:
                            if generation==self.generation:
                                self.record(key,label,result)
                                if key=='weather' and not result[1]:
                                    def solar_dependents(weather=result[0]):
                                        with ThreadPoolExecutor(max_workers=2) as secondary:
                                            follow={secondary.submit(fetch_alerts,weather):('alerts','NWS alerts'),secondary.submit(fetch_radar,weather):('radar','RainViewer radar')}
                                            for done in as_completed(follow):
                                                k,label=follow[done]
                                                with self.lock:
                                                    if generation==self.generation:self.record(k,label,done.result())
                                    threading.Thread(target=solar_dependents,daemon=True).start()
                                if key=='news' and not result[1]:
                                    self.news_day=now.date().isoformat()
                                    try:self.write_private(self.news_cache,json.dumps({'day':self.news_day,'items':result[0]}))
                                    except OSError:pass
                if config['sensor_file']:
                    try:
                        path=Path(config['sensor_file']).expanduser()
                        if path.stat().st_size>100000:raise ValueError('too large')
                        payload=json.loads(path.read_text())
                        with self.lock:
                            if generation==self.generation:
                                self.mutate({'action':'sensors','values':payload});self.record('sensors','Sensor file',(self.data['sensors'],None))
                    except Exception:
                        with self.lock:self.record('sensors','Sensor file',(None,'Cannot read valid sensor JSON.'))
            finally:
                with self.lock:self.busy=False;changed=generation!=self.generation
                if changed:self.refresh()
        threading.Thread(target=work,daemon=True).start()

    def load_demo(self):
        from demo import populate
        populate(self)

def fetch_commutes(config):
    result={}
    for name,origin,destination in [('work',config['commute_origin'],config['commute_destination']),('school',config['school_origin'],config['school_destination'])]:
        if not origin or not destination:continue
        try:
            response=requests.post('https://routes.googleapis.com/directions/v2:computeRoutes',headers={'X-Goog-Api-Key':config['routes_key'],'X-Goog-FieldMask':'routes.duration','Content-Type':'application/json'},json={'origin':{'address':origin},'destination':{'address':destination},'travelMode':'DRIVE','routingPreference':'TRAFFIC_AWARE'},timeout=(8,20))
            response.raise_for_status();duration=response.json()['routes'][0]['duration']
            seconds=float(duration.removesuffix('s'))
            if not 0<=seconds<604800:raise ValueError('Invalid duration')
            result[name]={'minutes':max(1,round(seconds/60)),'updated':stamp()}
        except Exception:result[name]={'error':'ETA unavailable. Check addresses, Routes API access, billing and quota.'}
    return result,None

def fetch_alerts(weather):
    try:
        response=requests.get('https://api.weather.gov/alerts/active',params={'point':f"{weather['latitude']},{weather['longitude']}"},headers={'User-Agent':'PersonalMirror/2.0 (local personal dashboard)','Accept':'application/geo+json'},timeout=(8,20));response.raise_for_status()
        return [{k:f['properties'].get(k) for k in ['event','severity','headline','description','instruction','expires']} for f in response.json()['features']],None
    except Exception:return None,'NWS alerts unavailable; consult official weather alerts.'

def fetch_radar(weather):
    try:
        response=requests.get('https://api.rainviewer.com/public/weather-maps.json',timeout=(8,20));response.raise_for_status()
        data=response.json();frames=data['radar']['past'][-6:]
        if not frames or any(not re.fullmatch(r'/v2/radar/[A-Za-z0-9_-]{1,128}',f['path']) for f in frames):raise ValueError('Invalid frames')
        return dict(frames=frames,host='https://tilecache.rainviewer.com',latitude=weather['latitude'],longitude=weather['longitude']),None
    except Exception:return None,'Radar unavailable; retry later.'

class Server(ThreadingHTTPServer):
    daemon_threads=True
    def __init__(self,address,store):self.store=store;super().__init__(address,Handler)
class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def response(self,status,body,content='application/json'):
        if status>=400 and isinstance(body,dict):self.server.store.log_error('Application',body.get('error','Request failed'))
        raw=json.dumps(body,default=encode).encode() if content=='application/json' else body
        self.send_response(status);self.send_header('Content-Type',content);self.send_header('Content-Length',str(len(raw)))
        self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.send_header('Referrer-Policy','strict-origin-when-cross-origin')
        self.send_header('X-Frame-Options','SAMEORIGIN');self.end_headers();self.wfile.write(raw)
    def authorized(self):
        host=urlparse('http://'+self.headers.get('Host','')).hostname
        try:valid=host=='localhost' or ipaddress.ip_address(host).is_loopback or ipaddress.ip_address(host).is_private
        except (ValueError,TypeError):valid=False
        origin=self.headers.get('Origin')
        if origin and origin!='http://'+self.headers.get('Host'):valid=False
        token=self.headers.get('Authorization','').removeprefix('Bearer ')
        return valid and hmac.compare_digest(token,self.server.store.token)
    def do_GET(self):
        path=urlparse(self.path).path
        if path=='/api/credentials':
            if not self.authorized():self.response(401,{'error':'Unauthorized request.'});return
            with self.server.store.lock:
                self.response(200,{'idrac_password':self.server.store.config['idrac_password'],'routes_key':self.server.store.config['routes_key'],'primary':self.server.store.password,'accounts':{a['id']:a['password'] for a in self.server.store.config['email_accounts']},'calendars':{c['id']:{k:c.get(k,'') for k in ['url','auth_password','auth_token']} for c in self.server.store.config['calendars']}})
            return
        if path=='/api/backup':
            if not self.authorized():self.response(401,{'error':'Unauthorized request.'});return
            self.response(200,{'csv':self.server.store.backup()});return
        if path=='/api/state':
            if not self.authorized():self.response(401,{'error':'Pair this browser using the launch link.'});return
            try:self.response(200,self.server.store.state())
            except Exception as error:
                print('Dashboard state error:',type(error).__name__,flush=True)
                self.response(500,{'error':'Dashboard data could not be processed ('+type(error).__name__+'). Restart with the latest version; settings are retained.'})
            return
        files={'/':'index.html','/app.js':'app.js','/style.css':'style.css'}
        if path not in files:self.response(404,{'error':'Not found'});return
        file=ROOT/'static'/files[path]
        self.response(200,file.read_bytes(),mimetypes.guess_type(file)[0] or 'text/plain')
    def do_POST(self):
        if not self.authorized():self.response(401,{'error':'Unauthorized request.'});return
        try:
            size=int(self.headers.get('Content-Length','0'))
            if not 0<size<=4_000_000:raise ValueError('Invalid request size.')
            body=json.loads(self.rfile.read(size))
            if not isinstance(body,dict):raise ValueError('Invalid request.')
            if self.path=='/api/refresh':self.server.store.refresh()
            elif self.path=='/api/action':self.server.store.mutate(body)
            else:self.response(404,{'error':'Not found'});return
            self.response(200,{'ok':True})
        except (ValueError,KeyError,TypeError) as error:self.response(400,{'error':str(error)})
        except Exception:self.response(500,{'error':'Could not save the change. Check file permissions.'})

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--lan',action='store_true',help='Allow access from devices on your trusted home network')
    parser.add_argument('--port',type=int,default=8765)
    parser.add_argument('--demo',action='store_true',help='Isolated sample data; never connects to accounts')
    parser.add_argument('--no-browser',action='store_true')
    parser.add_argument('--data-dir',type=Path,default=Path.home()/'.python_magic_mirror')
    args=parser.parse_args()
    directory=args.data_dir/'demo' if args.demo else args.data_dir
    store=Store(directory,args.demo);server=Server(('0.0.0.0' if args.lan else '127.0.0.1',args.port),store)
    url=f'http://127.0.0.1:{args.port}/#token={store.token}'
    print('Open this private pairing link on this computer:\n'+url,flush=True)
    if args.lan:print(f'Phone: use http://{store.local_ip}:{args.port}/#token={store.token}\nUse trusted Wi-Fi only. Do not port-forward this HTTP server.',flush=True)
    if not args.no_browser:webbrowser.open(url)
    stop=threading.Event()
    def scheduler():
        while not stop.is_set():
            store.refresh();stop.wait(store.config['refresh']*60)
    threading.Thread(target=scheduler,daemon=True).start()
    def hardware_monitor():
        while not stop.is_set():
            with store.lock:config=copy.deepcopy(store.config);generation=store.generation
            if not store.demo:
                try:result=fetch_idrac(config)
                except Exception:result=(None,'iDRAC monitor failed; verify automatic cooling on the server')
                with store.lock:
                    if generation==store.generation and config['idrac_enabled']:
                        store.record('idrac','iDRAC',result)
                        if result[0] and result[0].get('control',{}).get('message'):store.log_error('iDRAC cooling',result[0]['control']['message'])
            stop.wait(15)
    threading.Thread(target=hardware_monitor,daemon=True).start()
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:
        stop.set()
        try:restore_automatic()
        except Exception:print('WARNING: Could not restore automatic cooling. Check iDRAC.',flush=True)
        server.server_close()
if __name__=='__main__':main()




"""Deterministic-looking sample content, relative to today; never contacts services."""
from datetime import datetime,timedelta,time
from zoneinfo import ZoneInfo

def populate(store):
    c=store.config
    c.update(theme='lcars',auto_night=False,zip_code='35801',email_enabled=False,notes='Build something that matters.\n\nOne good decision at a time.',calendars=[],completed={})
    c['calendars']=[dict(id='demo',name='Google + Canvas sample',url='https://example.invalid/sample.ics',color='#cc99ff',enabled=True,assignments=True)]
    now=datetime.now(ZoneInfo(c['timezone']))
    def when(days=0,hour=10,minute=0):return datetime.combine(now.date()+timedelta(days=days),time(hour,minute),now.tzinfo).isoformat()
    c['classes']=[dict(id='ma171',title='Calculus I',days=[0,2,4],time='09:00',end='09:55',building='Shelby Center',room='Room 214'),dict(id='egr101',title='Engineering fundamentals',days=[1,3],time='13:30',end='14:45',building='Engineering Building',room='Lab 120')]
    c['countdowns']=[dict(id='exam',title='Calculus exam',target=when(5,9),category='School'),dict(id='engine',title='Engine stand test',target=when(12,10),category='Workshop'),dict(id='break',title='Semester break',target=when(28,0),category='Personal')]
    c['workshop']=[dict(id='w1',title='Inspect turbo oil feed',kind='Task',done=False,due=when(2),detail='Check fittings before the next run'),dict(id='w2',title='Radiator hose adapters',kind='Parts needed',done=False,due='',detail='Measure outlet diameter first'),dict(id='w3',title='Change break-in oil & inspect filter',kind='Maintenance',done=False,due=when(5),detail='Log oil temperature and pressure'),dict(id='w4',title='Verify cam timing logs',kind='Task',done=True,due='',detail='Baseline recorded')]
    c['manual_shipments']=[dict(id='p1',title='AN fittings + hose',carrier='Parts order',stage='Ordered',eta='Awaiting dispatch',updated=now.isoformat())]
    def event(key,title,start,assignment=False,source='Personal',location='',color='#cc99ff'):
        dt=datetime.fromisoformat(start)
        return dict(key=key,title=title,start=start,end=(dt+timedelta(hours=1)).isoformat(),assignment=assignment,source=source,location=location,color=color,all_day=False)
    events=[event('event1','Engineering study session',(now+timedelta(minutes=42)).isoformat(),location='Library • Room 204'),event('event2','Evening work shift',when(1,17),source='Work',color='#ffcc88'),event('event3','Engine stand test',when(2,11),source='Workshop',location='Garage',color='#f48c79'),event('a1','Calculus problem set',when(-1,23),True,'Canvas · MA 171'),event('a2','Engineering lab report',when(0,23,59),True,'Canvas · EGR 101'),event('a3','History discussion',when(2,23,59),True,'Canvas · HY 102'),event('a4','English reading response',when(4,23,59),True,'Canvas · EH 102')]
    c['completed']['a3']=True
    store.data['calendar:demo']=events
    store.data['weather']=dict(place='Huntsville, AL',latitude=34.73,longitude=-86.58,timezone='America/Chicago',current=dict(temperature_2m=58,apparent_temperature=56,relative_humidity_2m=64,weather_code=2,wind_speed_10m=6,time=now.replace(tzinfo=None).isoformat(timespec='minutes')),current_units={'wind_speed_10m':'mph'},daily=dict(temperature_2m_max=[65],temperature_2m_min=[44],sunrise=[when(0,6,23)[:16]],sunset=[when(0,16,42)[:16]]))
    store.data['email']=[dict(id='UPS:demo',title='Engine parts',carrier='UPS',number='DEMO TRACKING',status='In transit',eta='Expected tomorrow',date=now.isoformat(),link=''),dict(id='USPS:demo',title='Electronics order',carrier='USPS',number='DEMO TRACKING',status='Out for delivery',eta='Arriving today',date=now.isoformat(),link='')]
    store.data['news']=[dict(title='NASA Explores New Aerospace Technologies',url='https://www.nasa.gov/',published=now.isoformat(),source='NASA · sample headline')]
    store.data['alerts']=[]
    store.data['radar']={'demo':True,'latitude':34.73,'longitude':-86.58,'frames':[{'time':int(now.timestamp())-i*600,'path':'demo'} for i in range(5,-1,-1)]}
    store.data['sensors']=[dict(name='Oil temperature',value=155,unit='°F',updated=now.isoformat()),dict(name='Oil pressure',value=32,unit='psi',updated=now.isoformat()),dict(name='Engine speed',value=750,unit='rpm',updated=now.isoformat())]
    for key,label in [('calendar:demo','Google + Canvas'),('weather','ZIP weather'),('email','Shipment email'),('alerts','NWS alerts'),('radar','RainViewer radar')]:
        store.connections[key]={'label':label,'attempt':now.isoformat(),'success':now.isoformat(),'error':None,'sample':True}

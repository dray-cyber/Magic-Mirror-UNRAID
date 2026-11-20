import copy
from datetime import datetime
from email.message import EmailMessage
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch, MagicMock
from zoneinfo import ZoneInfo
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
import services as mirror
import services as extras
from mirror import Store,DEFAULT

NOW=datetime(2026,11,16,12,tzinfo=ZoneInfo('America/Chicago'))
SOURCE=dict(name='Classes',color='#ffffff',url='https://example.com/feed.ics')
def ics(events):
    return ('BEGIN:VCALENDAR\r\nVERSION:2.0\r\nPRODID:-//Mirror Test//EN\r\n'+events+'END:VCALENDAR\r\n').encode()
def vevent(fields):
    return 'BEGIN:VEVENT\r\n'+fields.replace('\n','\r\n')+'\r\nEND:VEVENT\r\n'
def email(subject,body,date='Mon, 16 Nov 2026 12:00:00 -0600'):
    msg=EmailMessage();msg['Subject']=subject;msg['From']='shop@example.com';msg['Date']=date
    msg['Message-ID']='<'+str(abs(hash(subject+date)))+'@test>'
    msg.set_content(body);return msg.as_bytes()

class CalendarTests(unittest.TestCase):
    def test_recurrence_exclusion_override(self):
        raw=ics(vevent('UID:recurring\nDTSTART:20261116T190000Z\nDTEND:20261116T200000Z\nRRULE:FREQ=DAILY;COUNT=4\nEXDATE:20261117T190000Z\nSUMMARY:Class')+
            vevent('UID:recurring\nRECURRENCE-ID:20261118T190000Z\nDTSTART:20261118T210000Z\nDTEND:20261118T220000Z\nSUMMARY:Moved class'))
        result=mirror.parse_events(raw,SOURCE,NOW,7)
        self.assertEqual(len(result),3)
        self.assertEqual(sorted(e['start'].day for e in result),[16,18,19])
        self.assertEqual(next(e for e in result if e['title']=='Moved class')['start'].hour,15)
        self.assertEqual(len({e['key'] for e in result}),3)
    def test_all_day_and_ongoing(self):
        raw=ics(vevent('UID:all\nDTSTART;VALUE=DATE:20261116\nDTEND;VALUE=DATE:20261117\nSUMMARY:Today')+
                vevent('UID:old\nDTSTART;VALUE=DATE:20261115\nDTEND;VALUE=DATE:20261116\nSUMMARY:Yesterday')+
                vevent('UID:ongoing\nDTSTART:20261116T170000Z\nDTEND:20261116T190000Z\nSUMMARY:Ongoing'))
        result=mirror.parse_events(raw,SOURCE,NOW,7)
        self.assertEqual({e['title'] for e in result},{'Today','Ongoing'})
        self.assertTrue(next(e for e in result if e['title']=='Today')['all_day'])
    def test_due_lookback_and_stable_key(self):
        raw=ics(vevent('UID:assignment\nDTSTART:20261115T180000Z\nSUMMARY:Homework'))
        self.assertEqual(mirror.parse_events(raw,SOURCE,NOW,7),[])
        source={**SOURCE,'assignments':True}
        first=mirror.parse_events(raw,source,NOW,7)[0]
        second=mirror.parse_events(raw.replace(b'20261115',b'20261117'),source,NOW,7)[0]
        self.assertTrue(first['assignment']);self.assertEqual(first['key'],second['key'])
    def test_cancelled(self):
        raw=ics(vevent('UID:cancelled\nDTSTART:20261117T180000Z\nSTATUS:CANCELLED\nSUMMARY:Cancelled'))
        self.assertEqual(mirror.parse_events(raw,SOURCE,NOW,7),[])
    def test_timezone_conversion_dst(self):
        raw=ics(vevent('UID:tz\nDTSTART:20261117T000000Z\nSUMMARY:Evening'))
        result=mirror.parse_events(raw,SOURCE,NOW,7)
        self.assertEqual(result[0]['start'].hour,18)
        self.assertEqual(result[0]['start'].day,16)
    def test_failures_do_not_expose_secret(self):
        with patch('mirror.requests.get',side_effect=mirror.requests.ConnectionError('https://secret.example/private-token')):
            events,error=mirror.fetch_calendar(SOURCE,NOW,7)
        self.assertEqual(events,[]);self.assertNotIn('token',error)

class ShipmentTests(unittest.TestCase):
    def test_ups_and_eta(self):
        result=extras.parse_shipment(email('Your package shipped','Tracking: 1Z999AA10123456784\nExpected delivery: November 18'))
        self.assertEqual(result[0]['carrier'],'UPS');self.assertEqual(result[0]['status'],'In transit')
        self.assertIn('November 18',result[0]['eta'])
        self.assertTrue(result[0]['link'].startswith('https://www.ups.com/'))
    def test_future_delivered_not_completed(self):
        result=extras.parse_shipment(email('Your package shipped','Your package will be delivered tomorrow. Tracking: 1Z999AA10123456784'))
        self.assertEqual(result[0]['status'],'In transit')
    def test_usps_requires_tracking_context(self):
        result=extras.parse_shipment(email('Package update','Tracking number: 9400111899223856928499'))
        self.assertEqual(result[0]['carrier'],'USPS')
        result=extras.parse_shipment(email('Package update','Order number: 9400111899223856928499'))
        self.assertEqual(result[0]['carrier'],'Unmatched notice')
    def test_html_no_remote_resources(self):
        msg=EmailMessage();msg['Subject']='Your package has been delivered';msg['From']='shop@example.com'
        msg.set_content('<html><style>hidden</style><p>Tracking: 1Z999AA10123456784</p><img src="https://example.com/pixel"></html>',subtype='html')
        result=extras.parse_shipment(msg.as_bytes())
        self.assertEqual(result[0]['status'],'Delivered');self.assertEqual(result[0]['carrier'],'UPS')
    def test_unrelated_email_ignored(self):
        self.assertEqual(extras.parse_shipment(email('Hello','Meeting at noon.')),[])
    def test_imap_readonly_and_newest_status(self):
        config={**extras.EXTRA_DEFAULTS,'email_enabled':True,'email_user':'user@example.com'}
        client=MagicMock();client.select.return_value=('OK',[b'2'])
        old=email('Your package shipped','Tracking: 1Z999AA10123456784','Sun, 15 Nov 2026 12:00:00 -0600')
        new=email('Your package has been delivered','Tracking: 1Z999AA10123456784')
        def uid(command,*args):
            if command=='search':return 'OK',[b'1 2']
            return 'OK',[(b'data',new if args[0]==b'2' else old)]
        client.uid.side_effect=uid
        with patch('services.imaplib.IMAP4_SSL',return_value=client):
            result,error=extras.fetch_shipments(config,'secret')
        self.assertIsNone(error);self.assertEqual(len(result),1);self.assertEqual(result[0]['status'],'Delivered')
        client.select.assert_called_once_with('"INBOX"',readonly=True)
        self.assertTrue(all('BODY.PEEK' in c.args[2] for c in client.uid.call_args_list if c.args[0]=='fetch'))
        client.logout.assert_called_once()
    def test_disabled_email_no_connection(self):
        with patch('services.imaplib.IMAP4_SSL') as connect:
            self.assertEqual(extras.fetch_shipments(extras.EXTRA_DEFAULTS,''),([],None))
            connect.assert_not_called()

class StorageWeatherTests(unittest.TestCase):
    def test_midnight_24_hour(self):
        midnight=NOW.replace(hour=0,minute=5)
        self.assertEqual(extras.clock_text(midnight,True),'00:05')
        self.assertEqual(extras.clock_text(midnight,False),'12:05 AM')

    def test_settings_round_trip(self):
        with tempfile.TemporaryDirectory() as directory:
            store=Store(directory)
            store.mutate({'action':'complete','key':'task','done':True})
            store.mutate({'action':'settings','values':{'theme':'blueprint','email_password':'secret'}})
            reloaded=Store(directory)
            self.assertTrue(reloaded.config['completed']['task'])
            self.assertEqual(reloaded.config['theme'],'blueprint')
            self.assertEqual(reloaded.password,'secret')
            self.assertNotIn('secret',json.dumps(store.state()))
    def test_weather_request_units_and_location(self):
        geo=MagicMock();geo.json.return_value={'places':[{'latitude':'34.73','longitude':'-86.58','place name':'Huntsville','state abbreviation':'AL'}]}
        weather=MagicMock();weather.json.return_value={'current':dict(temperature_2m=65,apparent_temperature=64,relative_humidity_2m=40,weather_code=0,wind_speed_10m=5,time='2026-11-16T12:00'),'daily':dict(temperature_2m_max=[70],temperature_2m_min=[50],sunrise=['2026-11-16T06:20'],sunset=['2026-11-16T16:40']),'current_units':{'wind_speed_10m':'mp/h'},'timezone':'America/Chicago'}
        with patch('services.requests.get',side_effect=[geo,weather]) as get:
            data,error=extras.fetch_weather({**extras.EXTRA_DEFAULTS,'zip_code':'35801'})
        self.assertIsNone(error);self.assertEqual(data['place'],'Huntsville, AL')
        params=get.call_args.kwargs['params']
        self.assertEqual(params['timezone'],'auto');self.assertIn('sunrise',params['daily'])
        self.assertNotIn('apikey',params)

if __name__=='__main__':unittest.main()

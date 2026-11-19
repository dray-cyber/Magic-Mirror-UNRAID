"""Public vendor health and unauthenticated reachability; no account credentials."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
import requests

GOOGLE='https://www.google.com/appsstatus/dashboard/incidents.json'
MICROSOFT='https://status.cloud.microsoft/api/posts/mac'
VENDORS={
 'gmail':('Gmail','https://mail.google.com/','https://www.google.com/appsstatus/dashboard/'),
 'outlook':('Outlook','https://outlook.office.com/','https://status.cloud.microsoft/m365'),
 'teams':('Teams','https://teams.microsoft.com/','https://status.cloud.microsoft/m365'),
}

def gmail_status(incidents):
    if not isinstance(incidents,list):raise ValueError('Unexpected Google status format')
    for incident in incidents:
        names=[p.get('title','') for p in incident.get('affected_products',[])]+[incident.get('service_name','')]
        if 'gmail' not in [name.lower() for name in names] or incident.get('end'):continue
        impact=incident.get('status_impact') or (incident.get('most_recent_update') or {}).get('status')
        if impact not in ('AVAILABLE',):return 'degraded'
    return 'operational'

def microsoft_status(post):
    if not isinstance(post,dict):raise ValueError('Unexpected Microsoft status format')
    status=str(post.get('Status','')).lower()
    if status=='available':return 'operational'
    if status in ('degraded','servicedegradation','serviceinterruption','unavailable','investigating','degradation','interruption'):return 'degraded'
    return 'unknown'

def fetch_service_health():
    def feed(url,parser):
        try:
            response=requests.get(url,timeout=(4,6),headers={'User-Agent':'MagicMirror/1.0 service-health'})
            response.raise_for_status();return parser(response.json())
        except (requests.RequestException,ValueError,TypeError,KeyError):return 'unknown'
    def reachable(url):
        try:
            response=requests.get(url,timeout=(4,6),headers={'User-Agent':'MagicMirror/1.0 service-health'},stream=True)
            try:return 'reachable' if 200<=response.status_code<400 else 'blocked' if response.status_code in (401,403,429) else 'unreachable'
            finally:response.close()
        except requests.RequestException:return 'unreachable'
    with ThreadPoolExecutor(max_workers=5) as pool:
        google=pool.submit(feed,GOOGLE,gmail_status);microsoft=pool.submit(feed,MICROSOFT,microsoft_status)
        checks={key:pool.submit(reachable,values[1]) for key,values in VENDORS.items()}
        statuses={'gmail':google.result(),'outlook':microsoft.result(),'teams':microsoft.result()}
        checked=datetime.now(timezone.utc).isoformat()
        return {key:dict(label=label,status=statuses[key],reachability=checks[key].result(),checked=checked,url=source,scope='Gmail public incidents' if key=='gmail' else 'Microsoft 365 broad public incidents') for key,(label,endpoint,source) in VENDORS.items()}

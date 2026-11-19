"""Read-only Dell iDRAC telemetry. Never sends fan-control/raw write commands."""
import os
import re
import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone

def parse_temperatures(text):
    rows=[]
    for line in text.splitlines():
        fields=[x.strip() for x in line.split('|')]
        name=fields[0]
        if not (re.search(r'cpu|processor',name,re.I) or len(fields)>3 and re.fullmatch(r'3\.\d+',fields[3])):continue
        match=re.search(r'(-?\d+(?:\.\d+)?)\s*degrees?\s*C',line,re.I)
        if match:rows.append({'name':name if name.lower()!='temp' else 'CPU '+fields[3].split('.')[-1],'celsius':float(match[1])})
    return rows

def parse_fans(text):
    rows=[]
    for line in text.splitlines():
        match=re.search(r'(\d+(?:\.\d+)?)\s*(RPM|percent|%)',line,re.I)
        if match:rows.append({'name':line.split('|')[0].strip(),'value':float(match[1]),'unit':'RPM' if match[2].upper()=='RPM' else '%'})
    return rows

def parse_energy(text):
    section=re.search(r'Cumulative Energy Consumption(.*?)(?=Statistic\s*:|\Z)',text,re.I|re.S)
    match=re.search(r'Reading\s*:\s*([\d,.]+)\s*kWh',section[1],re.I) if section else None
    return float(match[1].replace(',','')) if match else None

def fetch_idrac(config):
    if not config['idrac_enabled']:return None,None
    binary=shutil.which('ipmitool') or shutil.which('ipmitool.exe')
    if not binary:return None,'ipmitool is unavailable. Update the container image or install ipmitool on the Python host.'
    env=os.environ.copy();env['IPMI_PASSWORD']=config['idrac_password']
    base=[binary,'-I','lanplus','-H',config['idrac_host'],'-U',config['idrac_user'],'-E','-N','3','-R','1']
    commands={'temperatures':['sdr','type','temperature'],'fans':['sdr','type','fan'],'energy':['delloem','powermonitor']}
    def read(args):
        try:
            result=subprocess.run(base+args,env=env,shell=False,capture_output=True,text=True,timeout=12,check=True)
            return result.stdout
        except (subprocess.SubprocessError,OSError):return None
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures={key:pool.submit(read,args) for key,args in commands.items()}
        raw={key:f.result() for key,f in futures.items()}
    temperatures=parse_temperatures(raw['temperatures'] or '')
    fans=parse_fans(raw['fans'] or '')
    kwh=parse_energy(raw['energy'] or '')
    if not temperatures and not fans and kwh is None:return None,'Cannot read iDRAC telemetry. Check IP, credentials, IPMI-over-LAN and UDP 623 access.'
    missing=[]
    if not temperatures:missing.append('CPU temperatures')
    if not fans:missing.append('fan readings')
    if kwh is None:missing.append('cumulative kWh')
    return dict(temperatures=temperatures,fans=fans,kwh=kwh,updated=datetime.now(timezone.utc).isoformat(),warning='Unavailable: '+', '.join(missing) if missing else ''),None

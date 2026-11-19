"""Dell telemetry and explicitly enabled temperature-based fan control."""
import os
import re
import shutil
import subprocess
import math
import threading
import secrets
import copy
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
        fields=[part.strip() for part in line.split('|')]
        # Dell labels may themselves be "Fan1 RPM". Never parse the label.
        readings=fields[1:] if len(fields)>1 else [re.sub(r'^\s*fan\s*\d+\s*(?:RPM)?\s*[:=]?\s*','',line,flags=re.I)]
        for reading in readings:
            match=re.fullmatch(r'(\d+(?:\.\d+)?)\s*(RPM|percent|%)',reading,re.I)
            if match:
                rows.append({'name':fields[0],'value':float(match[1]),'unit':'RPM' if match[2].upper()=='RPM' else '%'})
                break
    return rows

def parse_energy(text):
    section=re.search(r'Cumulative Energy Consumption(.*?)(?=Statistic\s*:|\Z)',text,re.I|re.S)
    match=re.search(r'Reading\s*:\s*([\d,.]+)\s*kWh',section[1],re.I) if section else None
    return float(match[1].replace(',','')) if match else None

def _fetch_idrac(config):
    if not config['idrac_enabled']:
        pause_control();return None,None
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
    control=apply_control(config,temperatures,fans)
    missing=[]
    if not temperatures:missing.append('CPU temperatures')
    if not fans:missing.append('fan readings')
    if kwh is None:missing.append('cumulative kWh')
    return dict(control=control,fan_percent=control.get('percent',sum(f['value'] for f in fans if f['unit']=='%')/len([f for f in fans if f['unit']=='%']) if any(f['unit']=='%' for f in fans) else None),avg_fan_rpm=(sum(f['value'] for f in fans if f['unit']=='RPM')/len([f for f in fans if f['unit']=='RPM'])) if any(f['unit']=='RPM' for f in fans) else None,temperatures=temperatures,fans=fans,kwh=kwh,updated=datetime.now(timezone.utc).isoformat(),warning='Unavailable: '+', '.join(missing) if missing else ''),None


_control_lock=threading.RLock()
_controlled=None
_last_percent=None
_pending=None
_approved=50
_denied=False
_fingerprint=None

def fan_approval():
    with _control_lock:return copy.deepcopy(_pending)

def decide_fan(request_id,approve):
    global _pending,_approved,_denied
    with _control_lock:
        if not _pending or _pending['id']!=request_id:raise ValueError('Fan approval request changed; refresh and retry.')
        if type(approve) is not bool:raise ValueError('Invalid fan approval decision.')
        if approve:_approved=_pending['percent'];_denied=False
        else:_approved=50;_denied=True
        _pending=None

def command(config,args):
    binary=shutil.which('ipmitool') or shutil.which('ipmitool.exe')
    if not binary:raise RuntimeError('ipmitool unavailable')
    env=os.environ.copy();env['IPMI_PASSWORD']=config['idrac_password']
    return subprocess.run([binary,'-I','lanplus','-H',config['idrac_host'],'-U',config['idrac_user'],'-E','-N','3','-R','1']+args,env=env,shell=False,capture_output=True,text=True,timeout=8,check=True)

def pause_control():
    """Stop software ownership without changing the controller's manual setting."""
    global _controlled,_last_percent
    with _control_lock:
        _controlled=None;_last_percent=None

def connection_wait():
    """Quietly retain the last setting; disconnected readings never request 100%."""
    global _pending
    with _control_lock:
        _pending=None
        result={'mode':'waiting','message':'Reconnecting in background; last fan setting retained.'}
        if _last_percent is not None:result['percent']=_last_percent
        return result

def request_fault_approval(reason,temperatures):
    """Report faults without changing cooling until the user authorizes it."""
    global _pending
    if not _denied and (_pending is None or _pending['percent']<100):
        _pending={'id':secrets.token_hex(8),'percent':100,'cpu_c':max(temperatures) if temperatures else None,'reason':reason}
    result={'mode':'error','requested_percent':100,'message':reason+'; '+('increase denied' if _denied else 'awaiting approval')+'. Existing fan setting retained.'}
    if _last_percent is not None:result['percent']=_last_percent
    return result

def fan_target(config,temperatures):
    maximum=max(temperatures)
    if not math.isfinite(maximum) or maximum<0 or maximum>=config['fan_failsafe_c']:return None
    value=config['fan_min_percent']+max(0,maximum-config['fan_target_c'])*config['fan_gain']
    return min(100,max(config['fan_min_percent'],round(value)))

def apply_control(config,temperatures,fans):
    global _controlled,_last_percent,_pending,_approved,_denied,_fingerprint
    with _control_lock:
        fingerprint=tuple(config.get(k) for k in ['idrac_host','idrac_user','idrac_password','fan_min_percent','fan_target_c','fan_gain','fan_failsafe_c'])
        if fingerprint!=_fingerprint:
            _pending=None;_approved=50;_denied=False;_fingerprint=fingerprint
        if _controlled is not None and any(config[k]!=_controlled[k] for k in ['idrac_host','idrac_user','idrac_password']):pause_control()
        if not config.get('fan_control_enabled'):
            _pending=None;_approved=50;_denied=False
            pause_control()
            return {'mode':'paused','message':'Fan updates paused; controller retains its existing setting. Enable control to resume temperature monitoring.'}
        valid=[t['celsius'] for t in temperatures]
        if not valid or not fans:return connection_wait()
        target=fan_target(config,valid) if all(f['value']>0 for f in fans) else None
        fault_reason=None
        if target is None:
            fault_reason='CPU readings unavailable' if not valid else 'fan readings unavailable or stopped' if not fans or any(f['value']<=0 for f in fans) else 'temperature safety limit reached'
            if _approved<100 or _denied:return request_fault_approval(fault_reason,valid)
            target=100
        requested=target
        if target<=50:
            _approved=50;_denied=False
        elif target>_approved:
            if not _denied and _pending is None:
                _pending={'id':secrets.token_hex(8),'percent':target,'cpu_c':max(valid)}
            target=50
        try:
            # Retain ownership; a failed command must never trigger an unapproved increase.
            entering=_controlled is None
            _controlled=dict(config)
            if entering:command(config,['raw','0x30','0x30','0x01','0x00'])
            if entering or _last_percent!=target:command(config,['raw','0x30','0x30','0x02','0xff',hex(target)])
            _last_percent=target
            result={'mode':'manual','percent':target,'requested_percent':requested}
            if fault_reason:result['message']=fault_reason+'; user-approved fan speed.'
            if _pending:result['message']='Fan increase awaiting approval; manual speed limited to 50%.'
            elif _denied and requested>50:result['message']='Fan increase denied; manual speed limited to 50%.'
            return result
        except Exception:
            if entering:_controlled=None
            return connection_wait()

def fetch_idrac(config):
    with _control_lock:
        return _fetch_idrac(config)



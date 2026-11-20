"""Portable CSV settings. JSON values preserve types, commas and multiline strings."""
import csv
import io
import json

csv.field_size_limit(2_000_000)
FORMAT_VERSION=1

def export_csv(config,password):
    out=io.StringIO(newline='')
    writer=csv.writer(out)
    writer.writerow(['section','key','value'])
    writer.writerow(['meta','format_version',FORMAT_VERSION])
    for key,value in config.items():
        writer.writerow(['settings',key,json.dumps(value,ensure_ascii=False,separators=(',',':'))])
    writer.writerow(['credentials','email_password',json.dumps(password,ensure_ascii=False)])
    return out.getvalue()

def parse_csv(text):
    if not isinstance(text,str) or len(text)>2_000_000:raise ValueError('Choose a settings CSV smaller than 2 MB.')
    reader=csv.DictReader(io.StringIO(text.lstrip('\ufeff'),newline=''))
    if reader.fieldnames!=['section','key','value']:raise ValueError('Use a dashboard export with section,key,value columns.')
    settings={};password='';seen=set();version=None
    try:
        for row in reader:
            if None in row or any(v is None for v in row.values()):raise ValueError('Invalid CSV row.')
            section,key,value=row['section'],row['key'],row['value']
            if (section,key) in seen:raise ValueError('Duplicate CSV setting: '+key)
            seen.add((section,key))
            decoded=json.loads(value)
            if section=='meta' and key=='format_version':version=decoded
            elif section=='settings':settings[key]=decoded
            elif section=='credentials' and key=='email_password':
                if not isinstance(decoded,str):raise ValueError('Email password must be text.')
                password=decoded
            else:raise ValueError('Unknown CSV section or credential.')
    except (json.JSONDecodeError,csv.Error) as error:raise ValueError('CSV contains an invalid value; use an unmodified export.') from error
    if version!=FORMAT_VERSION:raise ValueError('Unsupported settings CSV version.')
    if not settings:raise ValueError('No settings found in CSV.')
    return settings,password

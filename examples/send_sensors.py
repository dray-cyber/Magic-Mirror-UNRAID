"""Example only. Supply real readings from your hardware acquisition software."""
import os
import requests

# Keep the pairing token in your environment rather than committing it to code.
token = os.environ['MIRROR_PAIRING_TOKEN']
response = requests.post('http://127.0.0.1:8765/api/action',
    headers={'Authorization': 'Bearer ' + token},
    json={'action':'sensors','values':[{'name':'Example pressure','value':32,'unit':'psi'}]},
    timeout=5)
response.raise_for_status()
print('Example reading sent')

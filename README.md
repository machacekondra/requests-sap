# requests-sap

A plugin to support SAP launchpad authentication in Python Requests.

## Usage

```python
import json
import os
import requests

from requests_sap import SAPAuth

r = requests.get(
    "https://launchpad.support.sap.com/services/odata/svt/swdcuisrv/ObjectSet('0030000000103162022')",
    auth=SAPAuth(username=os.environ['LP_USERNAME'], password=os.environ['LP_PASSWORD']),
    headers={'Accept': 'application/json'}
)

data = json.loads(r.text)
print(data['d']['Title'] + ' is ' + data['d']['Status'])
```

Output:
```bash
SAP HANA Platform Edt. 2.0 SPS05 rev57 Linux x86_64 is AVAILABLE
```

## Release

To build the project run:

```bash
make dist
```

To upload the project to pypi
```bash
make upload
```

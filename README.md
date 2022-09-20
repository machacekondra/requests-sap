# requests-sap

A plugin to support SAP launchpad authentication in Python Requests.

## Usage

```python
import requests

from requests_sap import SAPAuth

r = requests.get(
    "https://launchpad.support.sap.com/services/odata/svt/swdcuisrv/ObjectSet('0030000000103162022')",
    auth=SAPAuth(username='your_sap_username', password='your_sap_password'),
)

# Print the XML output of the Object ID:
print(r.text)
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

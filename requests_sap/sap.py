import requests
from requests.auth import AuthBase

from lxml import etree
import xml.etree.ElementTree as ET


class SAPAuth(AuthBase):
    """
    SAPAuth is class which implements the SAP launchpad authentication.
    """

    sso_url = 'https://accounts.sap.com/saml2/idp/sso'

    def get_next_url(self, text):
        return ET.fromstring(text, parser=etree.HTMLParser()).find(".//body//form[@method='post']").attrib['action']

    def get_all_inputs(self, text):
        ret = {}
        for i in ET.fromstring(text, parser=etree.HTMLParser()).findall(".//body//form[@method='post']//input"):
            if i.attrib.get('name') and i.attrib.get('value'):
                ret[i.attrib['name']] = i.attrib['value']

        return ret
    
    def __init__(self, username=None, password=None):
        self._username = username
        self._password = password

    def _next_step(self, response, history, next_url=None, **kwargs):
        if next_url is None:
            next_url = self.get_next_url(response.text)

        post_data = self.get_all_inputs(response.text)

        for k, v in kwargs.items():
            post_data[k] = v

        cookies = dict()
        for r in history:
            cookies = cookies | dict(r.cookies.items())

        next_response = requests.post(
            next_url,
            data=post_data,
            cookies=cookies,
        )

        history.append(next_response)

        return next_response

    def handle_response(self, response, **kwargs):
        history = [response]
        response = self._next_step(response, history)
        response = self._next_step(response, history, j_username=self._username)
        # We need to pass the next_url explicitly, because the response only contains relative URL for some reason:
        response = self._next_step(response, history, next_url=self.sso_url, j_password=self._password)
        response = self._next_step(response, history)
        return self._next_step(response, history)

    def __call__(self, request):
        request.register_hook('response', self.handle_response)
        return request

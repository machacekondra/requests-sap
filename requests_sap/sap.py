import json

import requests
from requests.auth import AuthBase

from lxml import etree
import xml.etree.ElementTree as ET

from urllib.parse import urlparse


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

    def _next_step(self, response, history, next_url=None, headers=None, **kwargs):
        if next_url is None:
            next_url = self.get_next_url(response.text)

        post_data = self.get_all_inputs(response.text)

        for k, v in kwargs.items():
            post_data[k] = v

        cookies = dict()
        for r in history:
            cookies.update(dict(r.cookies.items()))

        next_response = requests.post(
            next_url,
            data=post_data,
            cookies=cookies,
            headers=headers,
        )

        history.append(next_response)

        return next_response

    def _get_gigya_params(self, response):
        api_key = None
        saml_context = None
        for p in urlparse(response.url).query.split('&'):
            if p.startswith('samlContext='):
                saml_context = p[len('samlContext='):]
            elif p.startswith('apiKey='):
                api_key = p[len('apiKey='):]

        return saml_context, api_key

    def _get_login_token(self, history):
        response = requests.post(
            'https://core-api.account.sap.com/uid-core/authenticate?reqId=https://hana.ondemand.com/supportportal',
            json={'login': self._username, 'password': self._password},
            # For some reason requests/python user agent is not accepted:
            headers={'User-Agent': 'curl/7.82.0'},
        )
        history.append(response)
        data = json.loads(response.text)
        return data['cookieValue']

    def _get_saml_response(self, response, history):
        saml_context, api_key = self._get_gigya_params(response)
        login_token = self._get_login_token(history)

        response = requests.get(
            'https://cdc-api.account.sap.com/saml/v2.0/{0}/idp/sso/continue?loginToken={1}&samlContext={2}'.format(api_key, login_token, saml_context)
        )
        history.append(response)
        return response

    def _gigya(self, response, history):
        response = self._next_step(response, history)
        response = self._next_step(response, history, j_username=self._username)
        response = self._next_step(response, history)
        response = self._get_saml_response(response, history)
        response = self._next_step(response, history)
        response = self._next_step(response, history)
        return self._next_step(response, history, headers=self._headers)

    def handle_response(self, response, **kwargs):
        history = [response]

        if '@' in self._username:
            return self._gigya(response, history)

        response = self._next_step(response, history)
        response = self._next_step(response, history, j_username=self._username)
        # We need to pass the next_url explicitly, because the response only contains relative URL for some reason:
        response = self._next_step(response, history, next_url=self.sso_url, j_password=self._password)
        response = self._next_step(response, history)
        return self._next_step(response, history, headers=self._headers)

    def __call__(self, request):
        request.register_hook('response', self.handle_response)
        self._headers = request.headers
        return request

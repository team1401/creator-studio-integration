"""Server-only Agent Zero v2.14 UI API adapter; no browser credential access."""
import time
import uuid
import requests

class A0Client:
    def __init__(self, base_url, budget=70, timeout=20):
        if base_url != 'http://<agent-zero-host>:50080':
            raise ValueError('Worker URL not allowlisted')
        self.base = base_url
        self.session = requests.Session()
        self.session.trust_env = False
        self.budget, self.timeout = budget, timeout
        self.audit, self.owned = [], set()

    def request(self, method, path, **kwargs):
        if self.budget <= 0:
            raise RuntimeError('API request budget exhausted')
        self.budget -= 1
        start = time.monotonic()
        try:
            r = self.session.request(method, self.base + path, timeout=(5, self.timeout), allow_redirects=False, **kwargs)
        except requests.RequestException:
            self.audit.append({'method': method, 'path': path, 'error': 'transport_error'})
            raise RuntimeError('Agent Zero transport failure') from None
        self.audit.append({'method': method, 'path': path, 'status': r.status_code, 'seconds': round(time.monotonic()-start, 3)})
        return r

    def login(self, username, password):
        r = self.request('POST', '/login', data={'username': username, 'password': password})
        if r.status_code not in (302,303):
            raise RuntimeError('Login rejected')
        r = self.request('GET', '/api/csrf_token')
        if r.status_code != 200:
            raise RuntimeError('CSRF bootstrap rejected')
        token = r.json().get('token')
        if not token:
            raise RuntimeError('Missing CSRF token')
        self.session.headers.update({'X-CSRF-Token': token, 'Origin': self.base})

    def post(self, endpoint, payload):
        r = self.request('POST', '/api/' + endpoint, json=payload)
        if r.status_code != 200:
            raise RuntimeError('Agent Zero API rejected request: '+str(r.status_code))
        return r.json()

    def create(self):
        result = self.post('chat_create', {'project_name': ''})
        if not result.get('ok') or not result.get('ctxid'):
            raise RuntimeError('Context creation unconfirmed')
        self.owned.add(result['ctxid'])
        return result['ctxid']

    def _own(self, context):
        if not context or context not in self.owned:
            raise ValueError('Refusing mutation of unowned context')

    def send(self, context, text):
        self._own(context)
        return self.post('message_async', {'context': context, 'text': text, 'message_id': str(uuid.uuid4())})

    def poll(self, context=None):
        return self.post('poll', {'context': context, 'log_from': 0, 'notifications_from': 0})

    def pause(self, context):
        self._own(context)
        return self.post('pause', {'context': context, 'paused': True})

    def resume(self, context):
        self._own(context)
        return self.post('pause', {'context': context, 'paused': False})

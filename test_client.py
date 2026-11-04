import unittest
from unittest.mock import Mock
from a0_client import A0Client

class AdapterSafetyTests(unittest.TestCase):
    def setUp(self): self.c=A0Client('http://<agent-zero-host>:50080')
    def test_url_allowlist(self):
        for url in ('http://evil.invalid','http://<agent-zero-host>:50081','file:///etc/passwd'):
            with self.assertRaises(ValueError): A0Client(url)
    def test_existing_context_mutations_rejected(self):
        self.c.post=Mock()
        for ctx in ('','existing-user-job'):
            for fn in (self.c.pause,self.c.resume):
                with self.assertRaises(ValueError):fn(ctx)
            with self.assertRaises(ValueError):self.c.send(ctx,'hello')
        self.c.post.assert_not_called()
    def test_budget_stops_before_network(self):
        self.c.budget=0;self.c.session.request=Mock()
        with self.assertRaises(RuntimeError):self.c.request('GET','/')
        self.c.session.request.assert_not_called()
    def test_explicit_pause_resume_payload(self):
        self.c.owned.add('owned');self.c.post=Mock()
        self.c.pause('owned');self.c.post.assert_called_with('pause',{'context':'owned','paused':True})
        self.c.resume('owned');self.c.post.assert_called_with('pause',{'context':'owned','paused':False})
    def test_no_ambient_proxy_and_no_redirects(self):
        self.assertFalse(self.c.session.trust_env)
        self.c.session.request=Mock(return_value=Mock(status_code=200))
        self.c.request('GET','/')
        self.assertFalse(self.c.session.request.call_args.kwargs['allow_redirects'])
        self.assertEqual(self.c.session.request.call_args.kwargs['timeout'],(5,20))
    def test_audit_does_not_contain_payload(self):
        self.c.session.request=Mock(return_value=Mock(status_code=302))
        self.c.request('POST','/login',data={'password':'test-secret-sentinel'})
        self.assertNotIn('test-secret-sentinel',str(self.c.audit))

if __name__=='__main__':unittest.main()

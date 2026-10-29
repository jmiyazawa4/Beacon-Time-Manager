from pathlib import Path
import io
import json
import os
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import webapp


class SecurityTests(unittest.TestCase):
    def get(self,target,method='GET',extra=None):
        return webapp.dispatch(method,target,{'Host':'localhost',**(extra or {})})

    def test_source_configuration_and_directories_are_not_public(self):
        self.assertEqual(self.get('/')[0],200)
        self.assertEqual(self.get('/calendar-import.js')[0],200)
        for path in ['/server.py','/webapp.py','/daily_verse.py','/gunicorn.conf.py','/tests/test_security.py','/vendor/','/.env','/../README.md','/%2e%2e/server.py','/assets/../../server.py']:
            with self.subTest(path=path):self.assertEqual(self.get(path)[0],404)

    def test_security_headers_cover_successes_and_errors(self):
        for path in ['/','/server.py']:
            status,headers,body=self.get(path)
            csp=headers['Content-Security-Policy']
            self.assertIn("script-src 'self' 'sha256-",csp)
            self.assertNotIn('unsafe-eval',csp)
            self.assertIn("frame-ancestors 'none'",csp)
            self.assertIn("connect-src 'self'",csp)
            self.assertEqual(headers['Referrer-Policy'],'no-referrer')
            self.assertEqual(headers['X-Content-Type-Options'],'nosniff')
            self.assertEqual(headers['Cache-Control'],'no-store')
            self.assertNotIn('Access-Control-Allow-Origin',headers)
        with patch.dict(os.environ,{'BEACON_HTTPS':'1'}):
            self.assertIn('max-age=',self.get('/')[1]['Strict-Transport-Security'])

    def test_host_and_cross_site_api_guards(self):
        self.assertEqual(self.get('/',extra={'Host':'attacker.example'})[0],400)
        self.assertEqual(self.get('/api/verse',extra={'Sec-Fetch-Site':'cross-site'})[0],403)
        self.assertEqual(self.get('/api/verse',extra={'Origin':'https://attacker.example'})[0],403)
        with patch.dict(os.environ,{'BEACON_ALLOWED_HOSTS':'planner.example.edu'}):
            self.assertEqual(self.get('/',extra={'Host':'planner.example.edu'})[0],200)

    def test_no_uploads_or_planner_writes_and_wsgi_never_reads_body(self):
        for method in ['POST','PUT','PATCH','DELETE','OPTIONS']:
            self.assertEqual(self.get('/api/import',method)[0],405)
        class Unreadable:
            def read(self,*args):raise AssertionError('Personal request body was read')
        recorded=[]
        result=webapp.application({'REQUEST_METHOD':'POST','PATH_INFO':'/api/import','HTTP_HOST':'localhost','wsgi.input':Unreadable()},lambda status,headers:recorded.append(status))
        self.assertTrue(recorded[0].startswith('405'))
        self.assertIn(b'no planner data',result[0])

    def test_only_public_sport_parameter_reaches_source(self):
        with patch.object(webapp,'load_official_schedule',return_value={'events':[]}) as source:
            self.assertEqual(self.get('/api/schedule?sport=baseball')[0],200)
            source.assert_called_once_with('baseball')
            self.assertEqual(self.get('/api/schedule?sport=baseball&student=private')[0],400)
            self.assertEqual(source.call_count,1)
            self.assertEqual(self.get('/api/schedule?sport=https://attacker.example')[0],400)

    def test_busy_source_requests_are_bounded_and_errors_are_redacted(self):
        with patch.object(webapp.API_SLOTS,'acquire',return_value=False):
            result=self.get('/api/verse')
            self.assertEqual(result[0],429)
            self.assertEqual(result[1]['Retry-After'],'15')
        with patch.object(webapp,'load_verse',side_effect=ValueError('sensitive-internal-detail')):
            status,headers,body=self.get('/api/verse')
            self.assertEqual(status,502)
            self.assertNotIn(b'sensitive-internal-detail',body)

    def test_head_has_no_body_and_url_size_is_limited(self):
        status,headers,body=self.get('/','HEAD')
        self.assertEqual(status,200)
        self.assertEqual(body,b'')
        self.assertGreater(int(headers['Content-Length']),0)
        self.assertEqual(self.get('/'+'x'*2050)[0],414)


if __name__=='__main__':unittest.main()

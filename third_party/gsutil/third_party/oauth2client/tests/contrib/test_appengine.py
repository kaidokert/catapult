# Copyright 2014 Google Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
import httplib2
import json
import os
import tempfile
import time
import unittest2

from six.moves import urllib

import dev_appserver
dev_appserver.fix_sys_path()
import mock
import webapp2

from ..http_mock import CacheMock
from google.appengine.api import apiproxy_stub
from google.appengine.api import apiproxy_stub_map
from google.appengine.api import app_identity
from google.appengine.api import memcache
from google.appengine.api import users
from google.appengine.api.memcache import memcache_stub
from google.appengine.ext import db
from google.appengine.ext import ndb
from google.appengine.ext import testbed
from oauth2client.contrib import appengine
from oauth2client import GOOGLE_TOKEN_URI
from oauth2client import GOOGLE_REVOKE_URI
from oauth2client.clientsecrets import _loadfile
from oauth2client.clientsecrets import TYPE_WEB
from oauth2client.clientsecrets import InvalidClientSecretsError
from oauth2client.contrib.appengine import AppAssertionCredentials
from oauth2client.contrib.appengine import CredentialsModel
from oauth2client.contrib.appengine import CredentialsNDBModel
from oauth2client.contrib.appengine import CredentialsProperty
from oauth2client.contrib.appengine import FlowProperty
from oauth2client.contrib.appengine import (
    InvalidClientSecretsError as AppEngineInvalidClientSecretsError)
from oauth2client.contrib.appengine import OAuth2Decorator
from oauth2client.contrib.appengine import OAuth2DecoratorFromClientSecrets
from oauth2client.contrib.appengine import oauth2decorator_from_clientsecrets
from oauth2client.contrib.appengine import StorageByKeyName
from oauth2client.client import _CLOUDSDK_CONFIG_ENV_VAR
from oauth2client.client import AccessTokenRefreshError
from oauth2client.client import Credentials
from oauth2client.client import OAuth2Credentials
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import save_to_well_known_file
from webtest import TestApp


__author__ = 'jcgregorio@google.com (Joe Gregorio)'

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')


def datafile(filename):
    return os.path.join(DATA_DIR, filename)


def load_and_cache(existing_file, fakename, cache_mock):
    client_type, client_info = _loadfile(datafile(existing_file))
    cache_mock.cache[fakename] = {client_type: client_info}


class UserMock(object):
    """Mock the app engine user service"""

    def __call__(self):
        return self

    def user_id(self):
        return 'foo_user'


class UserNotLoggedInMock(object):
    """Mock the app engine user service"""

    def __call__(self):
        return None


class Http2Mock(object):
    """Mock httplib2.Http"""
    status = 200
    content = {
        'access_token': 'foo_access_token',
        'refresh_token': 'foo_refresh_token',
        'expires_in': 3600,
        'extra': 'value',
    }

    def request(self, token_uri, method, body, headers, *args, **kwargs):
        self.body = body
        self.headers = headers
        return self, json.dumps(self.content)


class TestAppAssertionCredentials(unittest2.TestCase):
    account_name = "service_account_name@appspot.com"
    signature = "signature"

    class AppIdentityStubImpl(apiproxy_stub.APIProxyStub):

        def __init__(self, key_name=None, sig_bytes=None,
                     svc_acct=None):
            super(TestAppAssertionCredentials.AppIdentityStubImpl,
                  self).__init__('app_identity_service')
            self._key_name = key_name
            self._sig_bytes = sig_bytes
            self._sign_calls = []
            self._svc_acct = svc_acct
            self._get_acct_name_calls = 0

        def _Dynamic_GetAccessToken(self, request, response):
            response.set_access_token('a_token_123')
            response.set_expiration_time(time.time() + 1800)

        def _Dynamic_SignForApp(self, request, response):
            response.set_key_name(self._key_name)
            response.set_signature_bytes(self._sig_bytes)
            self._sign_calls.append(request.bytes_to_sign())

        def _Dynamic_GetServiceAccountName(self, request, response):
            response.set_service_account_name(self._svc_acct)
            self._get_acct_name_calls += 1

    class ErroringAppIdentityStubImpl(apiproxy_stub.APIProxyStub):

        def __init__(self):
            super(TestAppAssertionCredentials.ErroringAppIdentityStubImpl,
                  self).__init__('app_identity_service')

        def _Dynamic_GetAccessToken(self, request, response):
            raise app_identity.BackendDeadlineExceeded()

    def test_raise_correct_type_of_exception(self):
        app_identity_stub = self.ErroringAppIdentityStubImpl()
        apiproxy_stub_map.apiproxy = apiproxy_stub_map.APIProxyStubMap()
        apiproxy_stub_map.apiproxy.RegisterStub('app_identity_service',
                                                app_identity_stub)
        apiproxy_stub_map.apiproxy.RegisterStub(
            'memcache', memcache_stub.MemcacheServiceStub())

        scope = 'http://www.googleapis.com/scope'
        credentials = AppAssertionCredentials(scope)
        http = httplib2.Http()
        self.assertRaises(AccessTokenRefreshError, credentials.refresh, http)

    def test_get_access_token_on_refresh(self):
        app_identity_stub = self.AppIdentityStubImpl()
        apiproxy_stub_map.apiproxy = apiproxy_stub_map.APIProxyStubMap()
        apiproxy_stub_map.apiproxy.RegisterStub("app_identity_service",
                                                app_identity_stub)
        apiproxy_stub_map.apiproxy.RegisterStub(
            'memcache', memcache_stub.MemcacheServiceStub())

        scope = [
            "http://www.googleapis.com/scope",
            "http://www.googleapis.com/scope2"]
        credentials = AppAssertionCredentials(scope)
        http = httplib2.Http()
        credentials.refresh(http)
        self.assertEqual('a_token_123', credentials.access_token)

        json = credentials.to_json()
        credentials = Credentials.new_from_json(json)
        self.assertEqual(
            'http://www.googleapis.com/scope http://www.googleapis.com/scope2',
            credentials.scope)

        scope = ('http://www.googleapis.com/scope '
                 'http://www.googleapis.com/scope2')
        credentials = AppAssertionCredentials(scope)
        http = httplib2.Http()
        credentials.refresh(http)
        self.assertEqual('a_token_123', credentials.access_token)
        self.assertEqual(
            'http://www.googleapis.com/scope http://www.googleapis.com/scope2',
            credentials.scope)

    def test_custom_service_account(self):
        scope = "http://www.googleapis.com/scope"
        account_id = "service_account_name_2@appspot.com"

        with mock.patch.object(app_identity, 'get_access_token',
                               return_value=('a_token_456', None),
                               autospec=True) as get_access_token:
            credentials = AppAssertionCredentials(
                scope, service_account_id=account_id)
            http = httplib2.Http()
            credentials.refresh(http)

            self.assertEqual('a_token_456', credentials.access_token)
            self.assertEqual(scope, credentials.scope)
            get_access_token.assert_called_once_with(
                [scope], service_account_id=account_id)

    def test_create_scoped_required_without_scopes(self):
        credentials = AppAssertionCredentials([])
        self.assertTrue(credentials.create_scoped_required())

    def test_create_scoped_required_with_scopes(self):
        credentials = AppAssertionCredentials(['dummy_scope'])
        self.assertFalse(credentials.create_scoped_required())

    def test_create_scoped(self):
        credentials = AppAssertionCredentials([])
        new_credentials = credentials.create_scoped(['dummy_scope'])
        self.assertNotEqual(credentials, new_credentials)
        self.assertTrue(isinstance(new_credentials, AppAssertionCredentials))
        self.assertEqual('dummy_scope', new_credentials.scope)

    def test_sign_blob(self):
        key_name = b'1234567890'
        sig_bytes = b'himom'
        app_identity_stub = self.AppIdentityStubImpl(
            key_name=key_name, sig_bytes=sig_bytes)
        apiproxy_stub_map.apiproxy = apiproxy_stub_map.APIProxyStubMap()
        apiproxy_stub_map.apiproxy.RegisterStub('app_identity_service',
                                                app_identity_stub)
        credentials = AppAssertionCredentials([])
        to_sign = b'blob'
        self.assertEqual(app_identity_stub._sign_calls, [])
        result = credentials.sign_blob(to_sign)
        self.assertEqual(result, (key_name, sig_bytes))
        self.assertEqual(app_identity_stub._sign_calls, [to_sign])

    def test_service_account_email(self):
        acct_name = 'new-value@appspot.gserviceaccount.com'
        app_identity_stub = self.AppIdentityStubImpl(svc_acct=acct_name)
        apiproxy_stub_map.apiproxy = apiproxy_stub_map.APIProxyStubMap()
        apiproxy_stub_map.apiproxy.RegisterStub('app_identity_service',
                                                app_identity_stub)

        credentials = AppAssertionCredentials([])
        self.assertIsNone(credentials._service_account_email)
        self.assertEqual(app_identity_stub._get_acct_name_calls, 0)
        self.assertEqual(credentials.service_account_email, acct_name)
        self.assertIsNotNone(credentials._service_account_email)
        self.assertEqual(app_identity_stub._get_acct_name_calls, 1)

    def test_service_account_email_already_set(self):
        acct_name = 'existing@appspot.gserviceaccount.com'
        credentials = AppAssertionCredentials([])
        credentials._service_account_email = acct_name

        app_identity_stub = self.AppIdentityStubImpl(svc_acct=acct_name)
        apiproxy_stub_map.apiproxy = apiproxy_stub_map.APIProxyStubMap()
        apiproxy_stub_map.apiproxy.RegisterStub('app_identity_service',
                                                app_identity_stub)

        self.assertEqual(app_identity_stub._get_acct_name_calls, 0)
        self.assertEqual(credentials.service_account_email, acct_name)
        self.assertEqual(app_identity_stub._get_acct_name_calls, 0)

    def test_get_access_token(self):
        app_identity_stub = self.AppIdentityStubImpl()
        apiproxy_stub_map.apiproxy = apiproxy_stub_map.APIProxyStubMap()
        apiproxy_stub_map.apiproxy.RegisterStub("app_identity_service",
                                                app_identity_stub)
        apiproxy_stub_map.apiproxy.RegisterStub(
            'memcache', memcache_stub.MemcacheServiceStub())

        credentials = AppAssertionCredentials(['dummy_scope'])
        token = credentials.get_access_token()
        self.assertEqual('a_token_123', token.access_token)
        self.assertEqual(None, token.expires_in)

    def test_save_to_well_known_file(self):
        os.environ[_CLOUDSDK_CONFIG_ENV_VAR] = tempfile.mkdtemp()
        credentials = AppAssertionCredentials([])
        self.assertRaises(NotImplementedError,
                          save_to_well_known_file, credentials)
        del os.environ[_CLOUDSDK_CONFIG_ENV_VAR]


class TestFlowModel(db.Model):
    flow = FlowProperty()


class FlowPropertyTest(unittest2.TestCase):

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()

        self.flow = flow_from_clientsecrets(
            datafile('client_secrets.json'),
            'foo',
            redirect_uri='oob')

    def tearDown(self):
        self.testbed.deactivate()

    def test_flow_get_put(self):
        instance = TestFlowModel(
            flow=self.flow,
            key_name='foo'
        )
        instance.put()
        retrieved = TestFlowModel.get_by_key_name('foo')

        self.assertEqual('foo_client_id', retrieved.flow.client_id)

    def test_make_value_from_datastore_none(self):
        self.assertIsNone(FlowProperty().make_value_from_datastore(None))

    def test_validate(self):
        FlowProperty().validate(None)
        self.assertRaises(
            db.BadValueError,
            FlowProperty().validate, 42)


class TestCredentialsModel(db.Model):
    credentials = CredentialsProperty()


class CredentialsPropertyTest(unittest2.TestCase):

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()

        access_token = 'foo'
        client_id = 'some_client_id'
        client_secret = 'cOuDdkfjxxnv+'
        refresh_token = '1/0/a.df219fjls0'
        token_expiry = datetime.datetime.utcnow()
        user_agent = 'refresh_checker/1.0'
        self.credentials = OAuth2Credentials(
            access_token, client_id, client_secret,
            refresh_token, token_expiry, GOOGLE_TOKEN_URI,
            user_agent)

    def tearDown(self):
        self.testbed.deactivate()

    def test_credentials_get_put(self):
        instance = TestCredentialsModel(
            credentials=self.credentials,
            key_name='foo'
        )
        instance.put()
        retrieved = TestCredentialsModel.get_by_key_name('foo')

        self.assertEqual(
            self.credentials.to_json(),
            retrieved.credentials.to_json())

    def test_make_value_from_datastore(self):
        self.assertIsNone(
            CredentialsProperty().make_value_from_datastore(None))
        self.assertIsNone(
            CredentialsProperty().make_value_from_datastore(''))
        self.assertIsNone(
            CredentialsProperty().make_value_from_datastore('{'))

        decoded = CredentialsProperty().make_value_from_datastore(
            self.credentials.to_json())
        self.assertEqual(
            self.credentials.to_json(),
            decoded.to_json())

    def test_validate(self):
        CredentialsProperty().validate(self.credentials)
        CredentialsProperty().validate(None)
        self.assertRaises(
            db.BadValueError,
            CredentialsProperty().validate, 42)


def _http_request(*args, **kwargs):
    resp = httplib2.Response({'status': '200'})
    content = json.dumps({'access_token': 'bar'})

    return resp, content


class StorageByKeyNameTest(unittest2.TestCase):

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        self.testbed.init_user_stub()

        access_token = 'foo'
        client_id = 'some_client_id'
        client_secret = 'cOuDdkfjxxnv+'
        refresh_token = '1/0/a.df219fjls0'
        token_expiry = datetime.datetime.utcnow()
        user_agent = 'refresh_checker/1.0'
        self.credentials = OAuth2Credentials(
            access_token, client_id, client_secret,
            refresh_token, token_expiry, GOOGLE_TOKEN_URI,
            user_agent)

    def tearDown(self):
        self.testbed.deactivate()

    def test_bad_ctor(self):
        with self.assertRaises(ValueError):
            StorageByKeyName(CredentialsModel, None, None)

    def test__is_ndb(self):
        storage = StorageByKeyName(
            object(), 'foo', 'credentials')

        self.assertRaises(
            TypeError, storage._is_ndb)

        storage._model = type(object)
        self.assertRaises(
            TypeError, storage._is_ndb)

        storage._model = CredentialsModel
        self.assertFalse(storage._is_ndb())

        storage._model = CredentialsNDBModel
        self.assertTrue(storage._is_ndb())

    def test_get_and_put_simple(self):
        storage = StorageByKeyName(
            CredentialsModel, 'foo', 'credentials')

        self.assertEqual(None, storage.get())
        self.credentials.set_store(storage)

        self.credentials._refresh(_http_request)
        credmodel = CredentialsModel.get_by_key_name('foo')
        self.assertEqual('bar', credmodel.credentials.access_token)

    def test_get_and_put_cached(self):
        storage = StorageByKeyName(
            CredentialsModel, 'foo', 'credentials', cache=memcache)

        self.assertEqual(None, storage.get())
        self.credentials.set_store(storage)

        self.credentials._refresh(_http_request)
        credmodel = CredentialsModel.get_by_key_name('foo')
        self.assertEqual('bar', credmodel.credentials.access_token)

        # Now remove the item from the cache.
        memcache.delete('foo')

        # Check that getting refreshes the cache.
        credentials = storage.get()
        self.assertEqual('bar', credentials.access_token)
        self.assertNotEqual(None, memcache.get('foo'))

        # Deleting should clear the cache.
        storage.delete()
        credentials = storage.get()
        self.assertEqual(None, credentials)
        self.assertEqual(None, memcache.get('foo'))

    def test_get_and_put_set_store_on_cache_retrieval(self):
        storage = StorageByKeyName(
            CredentialsModel, 'foo', 'credentials', cache=memcache)

        self.assertEqual(None, storage.get())
        self.credentials.set_store(storage)
        storage.put(self.credentials)
        # Pre-bug 292 old_creds wouldn't have storage, and the _refresh
        # wouldn't be able to store the updated cred back into the storage.
        old_creds = storage.get()
        self.assertEqual(old_creds.access_token, 'foo')
        old_creds.invalid = True
        old_creds._refresh(_http_request)
        new_creds = storage.get()
        self.assertEqual(new_creds.access_token, 'bar')

    def test_get_and_put_ndb(self):
        # Start empty
        storage = StorageByKeyName(
            CredentialsNDBModel, 'foo', 'credentials')
        self.assertEqual(None, storage.get())

        # Refresh storage and retrieve without using storage
        self.credentials.set_store(storage)
        self.credentials._refresh(_http_request)
        credmodel = CredentialsNDBModel.get_by_id('foo')
        self.assertEqual('bar', credmodel.credentials.access_token)
        self.assertEqual(credmodel.credentials.to_json(),
                         self.credentials.to_json())

    def test_delete_ndb(self):
        # Start empty
        storage = StorageByKeyName(
            CredentialsNDBModel, 'foo', 'credentials')
        self.assertEqual(None, storage.get())

        # Add credentials to model with storage, and check equivalent
        # w/o storage
        storage.put(self.credentials)
        credmodel = CredentialsNDBModel.get_by_id('foo')
        self.assertEqual(credmodel.credentials.to_json(),
                         self.credentials.to_json())

        # Delete and make sure empty
        storage.delete()
        self.assertEqual(None, storage.get())

    def test_get_and_put_mixed_ndb_storage_db_get(self):
        # Start empty
        storage = StorageByKeyName(
            CredentialsNDBModel, 'foo', 'credentials')
        self.assertEqual(None, storage.get())

        # Set NDB store and refresh to add to storage
        self.credentials.set_store(storage)
        self.credentials._refresh(_http_request)

        # Retrieve same key from DB model to confirm mixing works
        credmodel = CredentialsModel.get_by_key_name('foo')
        self.assertEqual('bar', credmodel.credentials.access_token)
        self.assertEqual(self.credentials.to_json(),
                         credmodel.credentials.to_json())

    def test_get_and_put_mixed_db_storage_ndb_get(self):
        # Start empty
        storage = StorageByKeyName(
            CredentialsModel, 'foo', 'credentials')
        self.assertEqual(None, storage.get())

        # Set DB store and refresh to add to storage
        self.credentials.set_store(storage)
        self.credentials._refresh(_http_request)

        # Retrieve same key from NDB model to confirm mixing works
        credmodel = CredentialsNDBModel.get_by_id('foo')
        self.assertEqual('bar', credmodel.credentials.access_token)
        self.assertEqual(self.credentials.to_json(),
                         credmodel.credentials.to_json())

    def test_delete_db_ndb_mixed(self):
        # Start empty
        storage_ndb = StorageByKeyName(
            CredentialsNDBModel, 'foo', 'credentials')
        storage = StorageByKeyName(
            CredentialsModel, 'foo', 'credentials')

        # First DB, then NDB
        self.assertEqual(None, storage.get())
        storage.put(self.credentials)
        self.assertNotEqual(None, storage.get())

        storage_ndb.delete()
        self.assertEqual(None, storage.get())

        # First NDB, then DB
        self.assertEqual(None, storage_ndb.get())
        storage_ndb.put(self.credentials)

        storage.delete()
        self.assertNotEqual(None, storage_ndb.get())
        # NDB uses memcache and an instance cache (Context)
        ndb.get_context().clear_cache()
        memcache.flush_all()
        self.assertEqual(None, storage_ndb.get())


class MockRequest(object):
    url = 'https://example.org'

    def relative_url(self, rel):
        return self.url + rel


class MockRequestHandler(object):
    request = MockRequest()


class DecoratorTests(unittest2.TestCase):

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        self.testbed.init_user_stub()

        decorator = OAuth2Decorator(client_id='foo_client_id',
                                    client_secret='foo_client_secret',
                                    scope=['foo_scope', 'bar_scope'],
                                    user_agent='foo')

        self._finish_setup(decorator, user_mock=UserMock)

    def _finish_setup(self, decorator, user_mock):
        self.decorator = decorator
        self.had_credentials = False
        self.found_credentials = None
        self.should_raise = False
        parent = self

        class TestRequiredHandler(webapp2.RequestHandler):
            @decorator.oauth_required
            def get(self):
                parent.assertTrue(decorator.has_credentials())
                parent.had_credentials = True
                parent.found_credentials = decorator.credentials
                if parent.should_raise:
                    raise parent.should_raise

        class TestAwareHandler(webapp2.RequestHandler):
            @decorator.oauth_aware
            def get(self, *args, **kwargs):
                self.response.out.write('Hello World!')
                assert(kwargs['year'] == '2012')
                assert(kwargs['month'] == '01')
                if decorator.has_credentials():
                    parent.had_credentials = True
                    parent.found_credentials = decorator.credentials
                if parent.should_raise:
                    raise parent.should_raise

        routes = [
            ('/oauth2callback', self.decorator.callback_handler()),
            ('/foo_path', TestRequiredHandler),
            webapp2.Route(r'/bar_path/<year:\d{4}>/<month:\d{2}>',
                          handler=TestAwareHandler, name='bar'),
        ]
        application = webapp2.WSGIApplication(routes, debug=True)

        self.app = TestApp(application, extra_environ={
            'wsgi.url_scheme': 'http',
            'HTTP_HOST': 'localhost',
        })
        self.current_user = user_mock()
        users.get_current_user = self.current_user
        self.httplib2_orig = httplib2.Http
        httplib2.Http = Http2Mock

    def tearDown(self):
        self.testbed.deactivate()
        httplib2.Http = self.httplib2_orig

    def test_in_error(self):
        # NOTE: This branch is never reached. _in_error is not set by any code
        # path. It appears to be intended to be set during construction.
        self.decorator._in_error = True
        self.decorator._message = 'foobar'

        response = self.app.get('http://localhost/foo_path')
        self.assertIn('foobar', response.body)

        response = self.app.get('http://localhost/bar_path/1234/56')
        self.assertIn('foobar', response.body)

    def test_callback_application(self):
        app = self.decorator.callback_application()
        self.assertEqual(
            app.router.match_routes[0].handler.__name__,
            'OAuth2Handler')

    def test_required(self):
        # An initial request to an oauth_required decorated path should be a
        # redirect to start the OAuth dance.
        self.assertEqual(self.decorator.flow, None)
        self.assertEqual(self.decorator.credentials, None)
        response = self.app.get('http://localhost/foo_path')
        self.assertTrue(response.status.startswith('302'))
        q = urllib.parse.parse_qs(
            response.headers['Location'].split('?', 1)[1])
        self.assertEqual('http://localhost/oauth2callback',
                         q['redirect_uri'][0])
        self.assertEqual('foo_client_id', q['client_id'][0])
        self.assertEqual('foo_scope bar_scope', q['scope'][0])
        self.assertEqual('http://localhost/foo_path',
                         q['state'][0].rsplit(':', 1)[0])
        self.assertEqual('code', q['response_type'][0])
        self.assertEqual(False, self.decorator.has_credentials())

        with mock.patch.object(appengine, '_parse_state_value',
                               return_value='foo_path',
                               autospec=True) as parse_state_value:
            # Now simulate the callback to /oauth2callback.
            response = self.app.get('/oauth2callback', {
                'code': 'foo_access_code',
                'state': 'foo_path:xsrfkey123',
            })
            parts = response.headers['Location'].split('?', 1)
            self.assertEqual('http://localhost/foo_path', parts[0])
            self.assertEqual(None, self.decorator.credentials)
            if self.decorator._token_response_param:
                response_query = urllib.parse.parse_qs(parts[1])
                response = response_query[
                    self.decorator._token_response_param][0]
                self.assertEqual(Http2Mock.content,
                                 json.loads(urllib.parse.unquote(response)))
            self.assertEqual(self.decorator.flow, self.decorator._tls.flow)
            self.assertEqual(self.decorator.credentials,
                             self.decorator._tls.credentials)

            parse_state_value.assert_called_once_with(
                'foo_path:xsrfkey123', self.current_user)

        # Now requesting the decorated path should work.
        response = self.app.get('/foo_path')
        self.assertEqual('200 OK', response.status)
        self.assertEqual(True, self.had_credentials)
        self.assertEqual('foo_refresh_token',
                         self.found_credentials.refresh_token)
        self.assertEqual('foo_access_token',
                         self.found_credentials.access_token)
        self.assertEqual(None, self.decorator.credentials)

        # Raising an exception still clears the Credentials.
        self.should_raise = Exception('')
        self.assertRaises(Exception, self.app.get, '/foo_path')
        self.should_raise = False
        self.assertEqual(None, self.decorator.credentials)

        # Access token refresh error should start the dance again
        self.should_raise = AccessTokenRefreshError()
        response = self.app.get('/foo_path')
        self.should_raise = False
        self.assertTrue(response.status.startswith('302'))
        query_params = urllib.parse.parse_qs(
            response.headers['Location'].split('?', 1)[1])
        self.assertEqual('http://localhost/oauth2callback',
                         query_params['redirect_uri'][0])

        # Invalidate the stored Credentials.
        self.found_credentials.invalid = True
        self.found_credentials.store.put(self.found_credentials)

        # Invalid Credentials should start the OAuth dance again.
        response = self.app.get('/foo_path')
        self.assertTrue(response.status.startswith('302'))
        query_params = urllib.parse.parse_qs(
            response.headers['Location'].split('?', 1)[1])
        self.assertEqual('http://localhost/oauth2callback',
                         query_params['redirect_uri'][0])

    def test_storage_delete(self):
        # An initial request to an oauth_required decorated path should be a
        # redirect to start the OAuth dance.
        response = self.app.get('/foo_path')
        self.assertTrue(response.status.startswith('302'))

        with mock.patch.object(appengine, '_parse_state_value',
                               return_value='foo_path',
                               autospec=True) as parse_state_value:
            # Now simulate the callback to /oauth2callback.
            response = self.app.get('/oauth2callback', {
                'code': 'foo_access_code',
                'state': 'foo_path:xsrfkey123',
            })
            self.assertEqual('http://localhost/foo_path',
                             response.headers['Location'])
            self.assertEqual(None, self.decorator.credentials)

            # Now requesting the decorated path should work.
            response = self.app.get('/foo_path')

            self.assertTrue(self.had_credentials)

            # Credentials should be cleared after each call.
            self.assertEqual(None, self.decorator.credentials)

            # Invalidate the stored Credentials.
            self.found_credentials.store.delete()

            # Invalid Credentials should start the OAuth dance again.
            response = self.app.get('/foo_path')
            self.assertTrue(response.status.startswith('302'))

            parse_state_value.assert_called_once_with(
                'foo_path:xsrfkey123', self.current_user)

    def test_aware(self):
        # An initial request to an oauth_aware decorated path should
        # not redirect.
        response = self.app.get('http://localhost/bar_path/2012/01')
        self.assertEqual('Hello World!', response.body)
        self.assertEqual('200 OK', response.status)
        self.assertEqual(False, self.decorator.has_credentials())
        url = self.decorator.authorize_url()
        q = urllib.parse.parse_qs(url.split('?', 1)[1])
        self.assertEqual('http://localhost/oauth2callback',
                         q['redirect_uri'][0])
        self.assertEqual('foo_client_id', q['client_id'][0])
        self.assertEqual('foo_scope bar_scope', q['scope'][0])
        self.assertEqual('http://localhost/bar_path/2012/01',
                         q['state'][0].rsplit(':', 1)[0])
        self.assertEqual('code', q['response_type'][0])

        with mock.patch.object(appengine, '_parse_state_value',
                               return_value='bar_path',
                               autospec=True) as parse_state_value:
            # Now simulate the callback to /oauth2callback.
            url = self.decorator.authorize_url()
            response = self.app.get('/oauth2callback', {
                'code': 'foo_access_code',
                'state': 'bar_path:xsrfkey456',
            })

            self.assertEqual('http://localhost/bar_path',
                             response.headers['Location'])
            self.assertEqual(False, self.decorator.has_credentials())
            parse_state_value.assert_called_once_with(
                'bar_path:xsrfkey456', self.current_user)

        # Now requesting the decorated path will have credentials.
        response = self.app.get('/bar_path/2012/01')
        self.assertEqual('200 OK', response.status)
        self.assertEqual('Hello World!', response.body)
        self.assertEqual(True, self.had_credentials)
        self.assertEqual('foo_refresh_token',
                         self.found_credentials.refresh_token)
        self.assertEqual('foo_access_token',
                         self.found_credentials.access_token)

        # Credentials should be cleared after each call.
        self.assertEqual(None, self.decorator.credentials)

        # Raising an exception still clears the Credentials.
        self.should_raise = Exception('')
        self.assertRaises(Exception, self.app.get, '/bar_path/2012/01')
        self.should_raise = False
        self.assertEqual(None, self.decorator.credentials)

    def test_error_in_step2(self):
        # An initial request to an oauth_aware decorated path should
        # not redirect.
        response = self.app.get('/bar_path/2012/01')
        url = self.decorator.authorize_url()
        response = self.app.get('/oauth2callback', {
            'error': 'Bad<Stuff>Happened\''
        })
        self.assertEqual('200 OK', response.status)
        self.assertTrue('Bad&lt;Stuff&gt;Happened&#39;' in response.body)

    def test_kwargs_are_passed_to_underlying_flow(self):
        decorator = OAuth2Decorator(client_id='foo_client_id',
                                    client_secret='foo_client_secret',
                                    user_agent='foo_user_agent',
                                    scope=['foo_scope', 'bar_scope'],
                                    access_type='offline',
                                    approval_prompt='force',
                                    revoke_uri='dummy_revoke_uri')
        request_handler = MockRequestHandler()
        decorator._create_flow(request_handler)

        self.assertEqual('https://example.org/oauth2callback',
                         decorator.flow.redirect_uri)
        self.assertEqual('offline', decorator.flow.params['access_type'])
        self.assertEqual('force', decorator.flow.params['approval_prompt'])
        self.assertEqual('foo_user_agent', decorator.flow.user_agent)
        self.assertEqual('dummy_revoke_uri', decorator.flow.revoke_uri)
        self.assertEqual(None, decorator.flow.params.get('user_agent', None))
        self.assertEqual(decorator.flow, decorator._tls.flow)

    def test_token_response_param(self):
        self.decorator._token_response_param = 'foobar'
        self.test_required()

    def test_decorator_from_client_secrets(self):
        decorator = OAuth2DecoratorFromClientSecrets(
            datafile('client_secrets.json'),
            scope=['foo_scope', 'bar_scope'])
        self._finish_setup(decorator, user_mock=UserMock)

        self.assertFalse(decorator._in_error)
        self.decorator = decorator
        self.test_required()
        http = self.decorator.http()
        self.assertEquals('foo_access_token',
                          http.request.credentials.access_token)

        # revoke_uri is not required
        self.assertEqual(self.decorator._revoke_uri,
                         'https://accounts.google.com/o/oauth2/revoke')
        self.assertEqual(self.decorator._revoke_uri,
                         self.decorator.credentials.revoke_uri)

    def test_decorator_from_client_secrets_toplevel(self):
        decorator_patch = mock.patch(
            'oauth2client.contrib.appengine.OAuth2DecoratorFromClientSecrets')

        with decorator_patch as decorator_mock:
            filename = datafile('client_secrets.json')
            decorator = oauth2decorator_from_clientsecrets(
                filename,
                scope='foo_scope')
            decorator_mock.assert_called_once_with(
                filename,
                'foo_scope',
                cache=None,
                message=None)

    def test_decorator_from_client_secrets_bad_type(self):
        # NOTE: this code path is not currently reachable, as the only types
        # that oauth2client.clientsecrets can load is web and installed, so
        # this test forces execution of this code path. Despite not being
        # normally reachable, this should remain in case future types of
        # credentials are added.

        loadfile_patch = mock.patch(
            'oauth2client.contrib.appengine.clientsecrets.loadfile')
        with loadfile_patch as loadfile_mock:
            loadfile_mock.return_value = ('badtype', None)
            self.assertRaises(
                AppEngineInvalidClientSecretsError,
                OAuth2DecoratorFromClientSecrets,
                'doesntmatter.json',
                scope=['foo_scope', 'bar_scope'])

    def test_decorator_from_client_secrets_kwargs(self):
        decorator = OAuth2DecoratorFromClientSecrets(
            datafile('client_secrets.json'),
            scope=['foo_scope', 'bar_scope'],
            approval_prompt='force')
        self.assertTrue('approval_prompt' in decorator._kwargs)

    def test_decorator_from_cached_client_secrets(self):
        cache_mock = CacheMock()
        load_and_cache('client_secrets.json', 'secret', cache_mock)
        decorator = OAuth2DecoratorFromClientSecrets(
            # filename, scope, message=None, cache=None
            'secret', '', cache=cache_mock)
        self.assertFalse(decorator._in_error)

    def test_decorator_from_client_secrets_not_logged_in_required(self):
        decorator = OAuth2DecoratorFromClientSecrets(
            datafile('client_secrets.json'),
            scope=['foo_scope', 'bar_scope'], message='NotLoggedInMessage')
        self.decorator = decorator
        self._finish_setup(decorator, user_mock=UserNotLoggedInMock)

        self.assertFalse(decorator._in_error)

        # An initial request to an oauth_required decorated path should be a
        # redirect to login.
        response = self.app.get('/foo_path')
        self.assertTrue(response.status.startswith('302'))
        self.assertTrue('Login' in str(response))

    def test_decorator_from_client_secrets_not_logged_in_aware(self):
        decorator = OAuth2DecoratorFromClientSecrets(
            datafile('client_secrets.json'),
            scope=['foo_scope', 'bar_scope'], message='NotLoggedInMessage')
        self.decorator = decorator
        self._finish_setup(decorator, user_mock=UserNotLoggedInMock)

        # An initial request to an oauth_aware decorated path should be a
        # redirect to login.
        response = self.app.get('/bar_path/2012/03')
        self.assertTrue(response.status.startswith('302'))
        self.assertTrue('Login' in str(response))

    def test_decorator_from_unfilled_client_secrets_required(self):
        MESSAGE = 'File is missing'
        try:
            decorator = OAuth2DecoratorFromClientSecrets(
                datafile('unfilled_client_secrets.json'),
                scope=['foo_scope', 'bar_scope'], message=MESSAGE)
        except InvalidClientSecretsError:
            pass

    def test_decorator_from_unfilled_client_secrets_aware(self):
        MESSAGE = 'File is missing'
        try:
            decorator = OAuth2DecoratorFromClientSecrets(
                datafile('unfilled_client_secrets.json'),
                scope=['foo_scope', 'bar_scope'], message=MESSAGE)
        except InvalidClientSecretsError:
            pass

    def test_decorator_from_client_secrets_with_optional_settings(self):
        # Test that the decorator works with the absense of a revoke_uri in
        # the client secrets.
        loadfile_patch = mock.patch(
            'oauth2client.contrib.appengine.clientsecrets.loadfile')
        with loadfile_patch as loadfile_mock:
            loadfile_mock.return_value = (TYPE_WEB, {
                "client_id": "foo_client_id",
                "client_secret": "foo_client_secret",
                "redirect_uris": [],
                "auth_uri": "https://accounts.google.com/o/oauth2/v2/auth",
                "token_uri": "https://www.googleapis.com/oauth2/v4/token",
                # No revoke URI
            })

            decorator = OAuth2DecoratorFromClientSecrets(
                'doesntmatter.json',
                scope=['foo_scope', 'bar_scope'])

        self.assertEqual(decorator._revoke_uri, GOOGLE_REVOKE_URI)
        # This is never set, but it's consistent with other tests.
        self.assertFalse(decorator._in_error)


class DecoratorXsrfSecretTests(unittest2.TestCase):
    """Test xsrf_secret_key."""

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()

    def tearDown(self):
        self.testbed.deactivate()

    def test_build_and_parse_state(self):
        secret = appengine.xsrf_secret_key()

        # Secret shouldn't change from call to call.
        secret2 = appengine.xsrf_secret_key()
        self.assertEqual(secret, secret2)

        # Secret shouldn't change if memcache goes away.
        memcache.delete(appengine.XSRF_MEMCACHE_ID,
                        namespace=appengine.OAUTH2CLIENT_NAMESPACE)
        secret3 = appengine.xsrf_secret_key()
        self.assertEqual(secret2, secret3)

        # Secret should change if both memcache and the model goes away.
        memcache.delete(appengine.XSRF_MEMCACHE_ID,
                        namespace=appengine.OAUTH2CLIENT_NAMESPACE)
        model = appengine.SiteXsrfSecretKey.get_or_insert('site')
        model.delete()

        secret4 = appengine.xsrf_secret_key()
        self.assertNotEqual(secret3, secret4)

    def test_ndb_insert_db_get(self):
        secret = appengine._generate_new_xsrf_secret_key()
        appengine.SiteXsrfSecretKeyNDB(id='site', secret=secret).put()

        site_key = appengine.SiteXsrfSecretKey.get_by_key_name('site')
        self.assertEqual(site_key.secret, secret)

    def test_db_insert_ndb_get(self):
        secret = appengine._generate_new_xsrf_secret_key()
        appengine.SiteXsrfSecretKey(key_name='site', secret=secret).put()

        site_key = appengine.SiteXsrfSecretKeyNDB.get_by_id('site')
        self.assertEqual(site_key.secret, secret)


class DecoratorXsrfProtectionTests(unittest2.TestCase):
    """Test _build_state_value and _parse_state_value."""

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()

    def tearDown(self):
        self.testbed.deactivate()

    def test_build_and_parse_state(self):
        state = appengine._build_state_value(MockRequestHandler(), UserMock())
        self.assertEqual(
            'https://example.org',
            appengine._parse_state_value(state, UserMock()))
        self.assertRaises(appengine.InvalidXsrfTokenError,
                          appengine._parse_state_value, state[1:], UserMock())


if __name__ == '__main__':  # pragma: NO COVER
    unittest2.main()

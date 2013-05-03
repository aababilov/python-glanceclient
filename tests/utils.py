# Copyright 2012 OpenStack LLC.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import urlparse
import requests

from glanceclient.openstack.common.apiclient import client as base_client


def assert_has_keys(dict, required=[], optional=[]):
    keys = dict.keys()
    for k in required:
        try:
            assert k in keys
        except AssertionError:
            extra_keys = set(keys).difference(set(required + optional))
            raise AssertionError("found unexpected keys: %s" %
                                 list(extra_keys))


class TestResponse(requests.Response):
    """
    Class used to wrap requests.Response and provide some
    convenience to initialize with a dict
    """

    def __init__(self, data):
        self._text = ""
        self._content_consumed = True
        super(TestResponse, self)
        if isinstance(data, dict):
            self.status_code = data.get('status_code', None)
            self.headers = data.get('headers',
                                    {"Content-Type": "application/json"})
            # Fake the text attribute to streamline Response creation
            self._text = data.get('text', "")
        else:
            self.status_code = data
        self._content = self._text

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    @property
    def text(self):
        return self._text


class FakeHttpClient(base_client.HttpClient):

    def __init__(self, *args, **kwargs):
        super(FakeHttpClient, self).__init__(
            username='username',
            password='password',
            tenant_id='tenant_id',
            tenant_name='tenant_name',
            auth_url='auth_url',
            endpoint='endpoint',
            token='token',
            region_name='name')

        self.callstack = []
        self.fixtures = kwargs.get("fixtures") or {}

    def assert_called(self, method, url, body=None, pos=-1):
        """
        Assert than an API method was just called.
        """
        expected = (method, url)
        called = self.callstack[pos][0:2]

        assert self.callstack, \
            "Expected %s %s but no calls were made." % expected

        assert expected == called, 'Expected %s %s; got %s %s' % \
            (expected + called)

        if body is not None:
            if self.callstack[pos][2] != body:
                raise AssertionError('%r != %r' %
                                     (self.callstack[pos][2], body))

    def assert_called_anytime(self, method, url, body=None):
        """
        Assert than an API method was called anytime in the test.
        """
        expected = (method, url)

        assert self.callstack, \
            "Expected %s %s but no calls were made." % expected

        found = False
        for entry in self.callstack:
            if expected == entry[0:2]:
                found = True
                break

        assert found, 'Expected %s %s; got %s' % \
            (expected, self.callstack)
        if body is not None:
            try:
                assert entry[2] == body
            except AssertionError:
                print(entry[2])
                print("!=")
                print(body)
                raise

        self.callstack = []

    def clear_callstack(self):
        self.callstack = []

    def authenticate(self):
        pass

    def cs_request(self, client, method, url, **kwargs):
        self.callstack.append((method, url,
                               kwargs.get("headers") or {},
                               kwargs.get('body', None)))
#        from nose.tools import set_trace; set_trace()
        fixture = self.fixtures[url][method]
        return TestResponse({"headers": fixture[0],
                             "text": fixture[1]}), fixture[1]

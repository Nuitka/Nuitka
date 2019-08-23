#     Copyright 2019, Tommy Li, mailto:tommyli3318@gmail.com
#
#     Python test originally created or extracted from other peoples work. The
#     parts from me are licensed as below. It is at least Free Software where
#     it's copied from other people. In these cases, that will normally be
#     indicated.
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
#


# nuitka-skip-unless-imports: requests

import requests
from unittest import mock

# This is the class we want to test
class myClass:
    def fetch_json(self, url):
        response = requests.get(url)
        return response.json()


# This method will be used by the mock to replace requests.get
def mocked_requests_get(*args, **kwargs):
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code

        def json(self):
            return self.json_data

    if args[0] == 'http://someurl.com/test.json':
        return MockResponse({"key1": "value1"}, 200)
    elif args[0] == 'http://someotherurl.com/anothertest.json':
        return MockResponse({"key2": "value2"}, 200)

    return MockResponse(None, 404)


# We patch 'requests.get' with our own method. The mock object is passed in to our test case method.
@mock.patch('requests.get', side_effect=mocked_requests_get)
def test_fetch(mock_get):
    # Assert requests.get calls
    mc = myClass()
    json_data = mc.fetch_json('http://someurl.com/test.json')
    print(json_data)
    assert json_data == {"key1": "value1"}

    json_data = mc.fetch_json('http://someotherurl.com/anothertest.json')
    print(json_data)
    assert json_data == {"key2": "value2"}

    json_data = mc.fetch_json('http://nonexistenturl.com/cantfindme.json')
    print(json_data)
    assert json_data is None


if __name__ == "__main__":
    test_fetch()
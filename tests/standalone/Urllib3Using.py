#     Copyright 2019, Kay Hayen, mailto:kay.hayen@gmail.com
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
import urllib3
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread

# nuitka-skip-unless-imports: urllib3

def runHTTPServer():
    class myServer(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == '/':
                self.path = '/index.html'
            try:
                file_to_open = open(self.path[1:]).read()
                self.send_response(200)
            except:
                file_to_open = 'File not found'
                self.send_response(404)
            self.end_headers()
            self.wfile.write(bytes(file_to_open,'utf-8'))

    server_address = ("127.0.0.1",8020)
    global server
    server = HTTPServer(server_address,myServer)
    server.serve_forever()

Thread(target=runHTTPServer).start()
print('Server started')

# testing request
http = urllib3.PoolManager()
r = http.request('GET', 'http://localhost:8020/')
# print response
print(r.status,r.data,r.headers)

# testing JSON content
import json
# make a temporary test file
with open('testjson.json','w') as f:
    f.write('{"origin": "128.195.97.166, 128.195.97.166"}')

r = http.request('GET', 'http://localhost:8020/testjson.json')
print(json.loads(r.data.decode('utf-8')))
os.remove('testjson.json')

server.shutdown()
print('Server shutdown')

# test ssl
import socket
import ssl
hostname = 'www.google.com'
context = ssl.create_default_context()
with socket.create_connection((hostname, 443)) as sock:
    with context.wrap_socket(sock, server_hostname=hostname) as ssock:
        print(ssock.version())

print('Reached end of file')


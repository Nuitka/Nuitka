import urllib3

# nuitka-skip-test-unless: urllib3

# testing request
http = urllib3.PoolManager()
r = http.request('GET', 'http://httpbin.org/robots.txt')
r = http.request('POST','http://httpbin.org/post',fields={'hello': 'world'})

# testing response
r.status
r.data
r.headers

# testing JSON content
import json
r = http.request('GET', 'http://httpbin.org/ip')
json.loads(r.data.decode('utf-8'))

# testing binary content
r = http.request('GET', 'http://httpbin.org/bytes/8')
r.data

print('Reached end of file')
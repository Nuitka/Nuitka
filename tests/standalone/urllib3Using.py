import urllib3
import json

http = urllib3.PoolManager()
r = http.request('GET', 'http://httpbin.org/robots.txt')
def test_data():
	'''Function to check for correctness of response data'''
	data = r.data
	decoded_data = data.decode('utf-8')
	assert decoded_data[:10] == 'User-agent'

r1 = http.request('GET', 'http://httpbin.org/ip')
def test_responses_r1():
	'''Function to ensure that correct ip address is returned'''
	assert r1.status == 200
	data1 = r1.data
	data1_decoded = data1.decode('utf-8')
	assert data1_decoded[5:11] == "origin"
	assert r1.headers['Content-Length'] == '49'

# for the data attribute of the request
r2 = http.request('GET', 'http://httpbin.org/ip')
def test_json_content():
	'''Function to test json content'''
	resp = json.loads(r2.data.decode('utf-8'))
	ip_addr = resp['origin'].split(',')
	assert ip_addr[0] == '154.72.168.147'

r3 = http.request('GET', 'http://httpbin.org/bytes/8')
def test_binary():
	'''Function to check binary data'''
	assert len(r3.data) == 8



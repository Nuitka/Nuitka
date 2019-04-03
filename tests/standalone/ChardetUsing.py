import urllib.request
import chardet

# nuitka-skip-unless-imports: chardet, urllib.request

rawdata = urllib.request.urlopen('http://yahoo.co.jp/').read()

def check_raw():
	'''function to check that the correct raw data is produced'''
	assert chardet.detect(rawdata)['confidence'] == 0.99
if __name__ == '__main__':
	check_raw()

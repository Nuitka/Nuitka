import urllib.request

test = urllib.request.urlopen('https://www.python.org')
print(test.read(300))
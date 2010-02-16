import urllib2

f = urllib2.urlopen('http://twitter2gtalk.appspot.com/list/')
result = f.read() 

users = result.split('!GP!')

for user in users:
    url = 'http://twitter2gtalk.appspot.com/update/?u=%s' % user
    
    f = urllib2.urlopen(url)
    result = f.read()

    print url
    print result

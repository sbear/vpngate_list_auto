#!env python
import urllib2
import re
import base64

vpn_list = 'http://enigmatic-scrubland-4484.herokuapp.com/'

# get serer list from list url
ua = urllib2.Request(vpn_list)
ua.add_header('User-agent', 'Mozilla/5.0')

res = urllib2.urlopen(ua)

if res.getcode() == 200 :
	print dir(res)
	#  deal every line , skip comment lines
	
	p = re.compile('^\w+')

	while True :
		svr_line = res.readline()
		if svr_line:
			if p.match(svr_line):
				c = re.compile(',').split(svr_line)
				ip = c[1]
				country = c[6]
				config_base64 = c[-1]
				config = base64.b64decode(config_base64)
				print ip, country, config
		else :
			break
	
	
else :
	print res.getcode()

#	print dir(res.geturl())
#	pprint(vars(res.info), indent=2)

#print res

#.read()
#print xxxdoa	q11``		 

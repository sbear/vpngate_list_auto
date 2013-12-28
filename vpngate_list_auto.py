#!env python
import urllib2
import re
import base64
import socket
import os, glob

vpn_list = 'http://enigmatic-scrubland-4484.herokuapp.com/'

# get serer list from list url
ua = urllib2.Request(vpn_list)
ua.add_header('User-agent', 'Mozilla/5.0')

res = urllib2.urlopen(ua)

def tcp_port_is_open(ip, port) :
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(1)
    r = s.connect_ex((ip, port))
    if r == 0 :
        s.close()
        return True
    else :
        return False



if res.getcode() == 200 :

    result = {}
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
#                print ip, country, config
                print ip, country

                # get tcp port from config_file
                p_tcp = re.compile('^proto tcp', re.MULTILINE)
                p_port = re.compile('^remote [.|\d]+ (\d+)', re.MULTILINE)
                if p_tcp.search(config) :
                    m_port = p_port.search(config)
                    if m_port :
                        port = int(m_port.group(1)) # 80 is num, '80' is str, it's different betwen perl and python
#                        print ip, port
                        if tcp_port_is_open(ip, port) :
                            print "GOOD: ", ip, port
                            if not country in result :
                                result[country] = []
                            else :
                                result[country].append({'ip':ip, 'config':config})
                            
                        else :
                            print "TIMEOUT: ", ip, port

        else :
            break
    
    #print result

    # rm old file
    config_path = 'C:\Program Files\OpenVPN\config'
    os.chdir(config_path)
    for conf in glob.glob('vpngate*.ovpn') :
        os.remove(conf)

    # write to file, every country limit 3 server
    for country in result :
        for server in result[country][0:3] :
#            print server
            file_name = '_'.join(['vpngate', country, server['ip']]) + '.ovpn'
            print file_name
            f = open(file_name, 'w')
            f.write(server['config'])
            f.close()

else :
    print res.getcode()


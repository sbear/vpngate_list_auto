#!env python
import urllib2
import re
import base64
import socket
import os, glob, sys, shutil
import threading
import Queue
import logging

vpn_list = 'http://enigmatic-scrubland-4484.herokuapp.com/'

def tcp_port_is_open(ip, port) :
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(1)
    r = s.connect_ex((ip, port))
    if r == 0 :
        s.close()
        return True
    else :
        return False

def udp_port_is_open(ip, port):
    pass


def save_config_file(result) :
    ''' '''

    os_str = sys.platform.lower()
    if os_str == 'darwin': # os x
        config_path = '/Users/%s/Library/Application Support/Tunnelblick/Configurations' % os.getlogin()
    elif os_str == 'win32':
        if os_bit == '64bit':
            config_path = 'C:\Program Files (x86)\OpenVPN\config'
        else:
            config_path = 'C:\Program Files\OpenVPN\config'
    else:
        logging.error("unkonw os type")


    # rm old config files
    os.chdir(config_path) # will auto die if chdir fail
    backup_dir = 'vpngate_old'

    if os.path.exists(backup_dir):
        shutil.rmtree(backup_dir)
    os.mkdir(backup_dir)

    # backup config files
    for item in glob.glob('vpngate*'):
        shutil.move(item, backup_dir)


    # save config file
    # write to file, every conutry limit 3 server
    for country in result:
        for server in result[country][0:3]:
            file_name = '_'.join(['vpngate', country, server['ip']]) + '.ovpn'
            print file_name
            f = open(file_name, 'w')
            f.write(server['config'])
            f.close

def get_config_content(vpn_lists):
    for vpn_list in vpn_lists:
        ua = urllib2.Request(vpn_list)
        ua.add_header('User-agent', 'Mozilla/5.0')
        res = urllib2.urlopen(ua)

        res_code = res.getcode()
        if res_code == 200:
            print 'web fetch ok'
            return res.read()
        else:
            logging.warn("vpn_list %s fetch error: %s" % (vpn_list, res_code))
            continue
    
    return None

def parse_config_content(content):
    '''
    res is web conntent handle
    parse all server, put into job queue
    '''
    svr_queue = Queue.Queue()
    p = re.compile('^\w+')
    p_newline = re.compile('\n')

    for svr_line in re.compile('\n').split(content):
        if svr_line:
            if p.match(svr_line):
                c = re.compile(',').split(svr_line)
                ip = c[1]
                country = c[6]
                config = base64.b64decode(c[-1])

                # get protocol, port from config
                p_proto = re.compile('^proto ((?:tcp)|(?:udp))', re.MULTILINE)
                p_port = re.compile('^remote [.|\d]+ (\d+)', re.MULTILINE)

                m_proto = p_proto.search(config)
                if m_proto:
                    proto = m_proto.group(1)

                    m_port = p_port.search(config)
                    if m_port:
                        port = m_port.group(1)


                        ## and server info into job queue
                        svr_queue.put((ip, proto, int(port), config, country))
          
                else:
                    logging.warn('Can"t find proto at like %s' % 'LINENUM')

    return svr_queue          
                

class WorkerThread(threading.Thread):
    def __init__(self, svr_queue, result_queue):
        threading.Thread.__init__(self)
        self.svr_queue = svr_queue
        self.result_queue = result_queue

    def run(self):
        while True:
            ip, proto, port, config, country = self.svr_queue.get()
            
            ava = False
            if proto == 'tcp':
                ava = tcp_port_is_open(ip, port)
            elif proto == 'udp':
                ava = udp_port_is_open(ip, port)
            else:
                logging.warn('ip:%s port:%s proto:%s error' % (ip, port, proto))

            if ava:
                self.result_queue.put((ip, proto, port, config, country))
            else:
                print "timeout ip:%s port %s" % (ip, port)
            self.svr_queue.task_done()
            print "done ip:%s, port:%s" % (ip, port)

def check_ava_svr(svr_queue):
    '''
    muiltiple thread 
    '''
    result_queue = Queue.Queue()

    t_num = 20
    for i in range(t_num):
        t = WorkerThread(svr_queue, result_queue)
        t.setDaemon(True)
        t.start()

    svr_queue.join()

    return result_queue


if __name__ == '__main__':
    vpn_lists = (vpn_list,)
    web_res = get_config_content(vpn_lists)

    svr_queue = parse_config_content(web_res)
    result_queue = check_ava_svr(svr_queue)

    result = {}
    while True:
        try:
            ip, proto, port, config, country = result_queue.get(block=False)
            print "Good: ip:%s port:%s proto:%s" % (ip, port, proto)
        except Exception as e:
            logging.info(e)
            break

        if not country in result:
            result[country] = []
        result[country].append({'ip':ip, 'port':port, 'proto':proto, 'config':config})

    save_config_file(result)



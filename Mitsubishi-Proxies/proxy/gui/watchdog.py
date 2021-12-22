 # coding=utf-8
import socket
import select
from multiprocessing import Process
import thread
import sys
import Queue 
import logging # reconstruct the code after
import json
from binascii import b2a_hex
import time
from binascii import *
import os
import subprocess
import thread
# data start with @, means command.

def get_pid(s):
    if len(s) == 0:
        return None
    idx = s.find(' ')
    start = end = 0
    for i in range(idx,len(s)):
        if s[i]!=' ':
            start = i
            break
    end = s.find(' ',start)
    return s[start:end]



def start_proxy():
    cmd = "python C:\\Users\\fdl\\Desktop\\Mitsubishi\\proxy\\network\\proxy.py"
    # proc = subprocess.Popen(cmd,shell=True)
    # proc.communicate()
    # print('in thread, start a program')
    os.system(cmd)

def start_driver():
    cmd = "python C:\\Users\\fdl\\Desktop\\Mitsubishi\\proxy\\gui\\driver.py"
    os.system(cmd)

def get_service_pid(s):
    # print(s)
    if len(s) == 0:
        return None
    idx = s.find("LISTENING")
    start = end = 0
    for i in range(idx, len(s)):
        if s[i] == ' ':
            start = i
        end = s.find('\n', start)
    print('start:{},end:{}'.format(start,end))
    return s[start:end].strip(' ')

def kill_service(port):
    cmd = "netstat -ano|findstr :{}".format(port)
    proc = subprocess.Popen(cmd,shell=True,stdin=subprocess.PIPE,stdout=subprocess.PIPE)
    output = proc.communicate()[0]
    target_pid = get_service_pid(output)
    if target_pid is not None:
        cmd = "taskkill /PID {} /F".format(target_pid)
        os.system(cmd)
        print('killed the proxy_pid')


def restart_service():
    kill_service(5007)
    kill_service(65534)

    proxy_process = Process(target=start_proxy,args=())
    driver_process = Process(target=start_driver,args=())
    proxy_process.start()
    driver_process.start()

def kill_target_process():
    cmd = "tasklist|findstr dw20.exe*"
    proc = subprocess.Popen(cmd,shell=True,stdin=subprocess.PIPE,stdout=subprocess.PIPE)
    output = proc.communicate()[0]
    target_pid = get_pid(output)
    print("dw20.exe pid:{}".format(target_pid))
    if target_pid is not None:
        cmd = "taskkill /PID {} /F".format(target_pid)
        os.system(cmd)
        print('killed the target_pid')

    cmd = "tasklist|findstr GD2*"
    proc = subprocess.Popen(cmd,shell=True,stdin=subprocess.PIPE,stdout=subprocess.PIPE)
    output = proc.communicate()[0]
    target_pid = get_pid(output)
    print("GD2.exe pid:{}".format(target_pid))
    if target_pid is not None:
        cmd = "taskkill /PID {} /F".format(target_pid)
        os.system(cmd)
        print('killed the target_pid')
    # print([get_pid(output)])
    cmd = "tasklist|findstr ECMonitor*"
    proc = subprocess.Popen(cmd,shell=True,stdin=subprocess.PIPE,stdout=subprocess.PIPE)
    output = proc.communicate()[0]
    target_pid = get_pid(output)
    print("ECMonitor* pid:{}".format(target_pid))
    if target_pid is not None:
        cmd = "taskkill /PID {} /F".format(target_pid)
        os.system(cmd)
        print('killed the target_pid')

def kill_utility():
    cmd = "tasklist|findstr mit_*"
    proc = subprocess.Popen(cmd,shell=True,stdin=subprocess.PIPE,stdout=subprocess.PIPE)
    output = proc.communicate()[0]
    process_infos = output.split('\r\n')
    for item in process_infos:
        m_pid = get_pid(item)
        if m_pid is not None:
            cmd = "taskkill /PID {} /F".format(m_pid)
            os.system(cmd)
            print("killed pid:{}".format(m_pid))
    kill_target_process()

def restart_utility():
    kill_utility()
    # detector_process = Process(target=launch_detector,args=())
    # detector_process.start()


def reset_environment():
    logging.debug("reset environment start......")
    restart_service()
    restart_utility()
    logging.debug("reset environment complete......")
    

class proxy(object):
    
    def __init__(self, sock):
        self.BUFSIZE = 10000
        self.server = sock
        self.inputs = [self.server] 
        self.sock_dict = {} # record for controller, software, and device 
     

    def socket_send(sock,data,tag):
        logging.debug("in process:{}".format(tag))
        try:
            sock.send(data)
            time.sleep(0.1) # in case send two stream as one stream
        except Exception as exp:
            err = "{}:{}".format(tag,exp)
            logging.warning(err)

    def run(self):
        self.noblocking()
    
    
    def noblocking(self, timeout=10):
        while True:
            try:
                readable,_,exceps = select.select(self.inputs,[],self.inputs,timeout) 
                for soc in readable:
                    if soc is self.server: 
                        # proactive connect to to proxy, [controller,software], device should notify
                        client_con, _ = soc.accept() 
                        self.inputs.append(client_con)
                        logging.debug("connect success:{}".format(client_con.getpeername()))

                    else: 
                        data = soc.recv(self.BUFSIZE)

                        # socket is ok!
                        if data != "": 
                            logging.debug("cmd:{}".format(data))
                            if data == "reset":
                                reset_environment()   
                        # socket closed by peer
                        else: 
                            if soc in self.inputs:
                                self.inputs.remove(soc)
                            logging.debug("socket is closed by peer")
                                                
                for exp in exceps:
                    # maybe server?
                    logging.warning('Exception:{}'.format(exp.getpeername()))
                    if exp in self.inputs:
                        self.inputs.remove(exp)

            except Exception as error:
                logging.warning("Error info:{}".format(error))
                errMsg = "{}".format(error)
                if soc in self.inputs:
                    self.inputs.remove(soc)              


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG) # can show debug info

    # reset_environment()
    
    ADDR = ("0.0.0.0",65533)
    
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(ADDR)
    server.listen(10)
    p = proxy(server)
    p.run()

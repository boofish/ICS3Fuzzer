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
import win32evtlog


# data start with @, means command.

def detect_crash(record_number):
    logging.debug("in detect_crash:{}".format(record_number))
    record_number = int(record_number)
    h=win32evtlog.OpenEventLog(None, "Application")
    flags = win32evtlog.EVENTLOG_BACKWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ
    records = win32evtlog.ReadEventLog(h,flags,0)
    newest_number = records[0].RecordNumber
    ret = "no"

    for item in records:
        event_number = item.RecordNumber
        if event_number <= record_number:
            break
        source_name = item.SourceName
        if item.SourceName == "Application Error" or item.SourceName == "Application Hang":
            ret = "yes"
            break

    result = "{}:{}".format(ret, str(newest_number))
    return result
    

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
                            start = time.time()

                            if data == "launch":

                                r = os.system(".\\utils\\mit_execute_drrun.exe")
                                # r = os.system(".\\utils\\launch.exe")

                            elif data == "kill":
                                r = os.system("python ./utils/kill_gxworks.py")

                            elif data.find("detect")>=0:
                                parmeter = data[7:]
                                r = detect_crash(parmeter)

                            elif data.find("operation") >=0:
                                cmd = ".\\utils\\" +  data[data.find(':')+1:]
                                r = 'operation->' + str(os.system(cmd))
                                logging.debug('execute cmd result:{}'.format(r))
                            else:
                                logging.debug("error in cmd")
                                r = "error"

                            end = time.time()
                            logging.debug("time consumed:{}!".format(end-start))
                            soc.send(str(r))
                            
                        # socket closed by peer
                        else: 
                            self.inputs.remove(soc)

                            logging.debug("socket is closed by peer")
                                                
                for exp in exceps:
                    # maybe server?
                    logging.warning('Exception:{}'.format(exp.getpeername()))
                    self.inputs.remove(exp)

            except Exception as error:
                logging.warning("Error info:{}".format(error))
                errMsg = "{}".format(error)
                self.inputs.remove(soc)              


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG) # can show debug info
    
    ADDR = ("0.0.0.0",65534)
    
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(ADDR)
    server.listen(10)
    p = proxy(server)
    p.run()

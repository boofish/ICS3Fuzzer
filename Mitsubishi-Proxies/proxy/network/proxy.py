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


# data start with @, means command.




class proxy(object):
    
    def __init__(self, sock):
        self.BUFSIZE = 10000
        
        self.server = sock
        self.inputs = [self.server]
        self.recv_queue = [] # recv data from device
        self.send_queue = [] # send data from software
        self.sock_dict = {} # record for controller, software, and device 
        self.sock_dict["software"] = None
        self.sock_dict["device"] = None  # record for target connect
        self.sock_dict["controller"] = None
        

    def ctl_start_fuzzing(self):
        # fuzzing_data = client_sock.recv(self.BUFSIZE)
        # start_fuzzing(fuzzing_data)
        logging.debug("start fuzzing!")

    @staticmethod
    def socket_send(sock,data,tag):
        logging.debug("in process:{}".format(tag))
        try:
            sock.send(data)
            time.sleep(0.01) # in case send two stream as one stream
        except Exception as exp:
            err = "{}:{}".format(tag,exp)
            logging.warning(err)


    # controller cmd: send data to controller
    # one time only extract one instance.
    def ctl_extract_recvData(self):
        logging.debug("extract recvdata from cache")
        ctl_sock = self.sock_dict["controller"]
        if not ctl_sock:
            logging.critical("controller sock is not add to sock_dict!")

        if not len(self.recv_queue)==0:
            data = self.recv_queue[0] # get data but not remove
            self.socket_send(ctl_sock, data,"extract_recvData")
        else:
            self.socket_send(ctl_sock,"empty","extract_recvData")
            logging.debug("recvdata has empty cache")

    def ctl_get_sendData(self):
        logging.debug("extract sendData from software")
        ctl_sock = self.sock_dict["controller"]

        if not ctl_sock:
            logging.critical("controller sock is add to sock_dict!")

        if not len(self.send_queue) == 0:
            data = self.send_queue[0] # get data and remove
            self.send_queue.remove(data)
            self.socket_send(ctl_sock, data, "ctl_get_sendData")
        else:
            self.socket_send(ctl_sock,"empty","ctl_get_sendData")
            logging.debug("send_queue has empty data")
    
    # controller cmd: send data from proxy to software
    def ctl_forward_data(self):
        if len(self.recv_queue) == 0:
            logging.warning("ctl_forward_data did not have data on cache!")
            return 
        try:
            cache_data = self.recv_queue[0]
            self.recv_queue.remove(cache_data)
            self.sock_dict["software"].send(cache_data)
            time.sleep(0.01) # in case two pkt concreate to one
        except Exception as exp:
            self.recv_queue.insert(0,cache_data)
            logging.critical("ctl_forward_data error:{}".format(exp))
    
    # controller cmd: send data from proxy to software
    def ctl_modify_data(self,data):
        ctl_sock = self.sock_dict["software"]
        if len(self.recv_queue) <= 0:
            logging.warning("Empty,cannot feeding data to software")
        else:
            self.recv_queue.remove(self.recv_queue[0])
            self.socket_send(ctl_sock, data, "modifing_data_to_software")

    # controller cmd: send data from proxy to controller
    def ctl_extract_stats(self):
        msg = {}
        ctl_sock = self.sock_dict["controller"]
        if self.sock_dict["software"]:
            msg["software"] = "on"
        else:
            msg["software"] = "off"
        if self.sock_dict["device"]:
            msg["device"] = "on"
        else:
            msg["device"] = "off"
        msg["buf_cnt"] = len(self.recv_queue)
        
        ctl_sock.send(json.dumps(msg))

        
    # from device role, sending data from proxy to device
    def device_data_feeding(self,device_sock,data):
        try:
            device_sock.send(data)
        except Exception as exp:
            errMsg = "device_data_feeding_error:{}".format(exp)
            logging.warning(errMsg)
            
            

    def close_software(self):
        if self.sock_dict["software"] is not None:
            if self.sock_dict["software"] in self.inputs:
                self.inputs.remove(self.sock_dict["software"])
                self.sock_dict["software"].close()
                self.sock_dict["software"] = None
                self.recv_queue = []

        if self.sock_dict["device"] is not None:
            if self.sock_dict["device"] in self.inputs:

                self.inputs.remove(self.sock_dict["device"])
                self.sock_dict["device"].close()
                self.sock_dict["device"] = None
            

    def run(self):
        self.noblocking()
    
    def __clear_recv_queue(self):
        self.recv_queue = []
        logging.debug("clear recv_queue over!")
    
    def handle_request_from_controller(self,data):
        header = data[:6] # @fuzz:/@recv:/@logs:/@fwrd:
        remaining = data[6:]

        if header.find('@')>=0 and header.find(':')>=0:
            if header == "@fuzz:":
                self.ctl_start_fuzzing()

            elif header == "@recv:":
                self.ctl_extract_recvData()

            elif header == "@fwrd:": # forward to software
                self.ctl_forward_data()

            elif header == "@stat:":
                self.ctl_extract_stats()

            elif header == "@mdfy:":
                self.ctl_modify_data(remaining)

            elif header == "@clos:":
                self.close_software()

            elif header == "@insp:":
                self.ctl_get_sendData()

            else:
                logging.debug("error header:{}".format(header))
        else:# error format request
            logging.warning("dataFormat_from_controller_wrong:{}".format(data))

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
                        logging.debug("new connect, self.inputs length:{}".format(len(self.inputs)))

                    else: 
                        data = soc.recv(self.BUFSIZE)
                        # recognize connection from software or controller
                        if data == "iamcontroller":
                            logging.debug("role_is_controller")
                            logging.debug("self controller?:{}".format(self.sock_dict["controller"]))
                            self.sock_dict["controller"] = soc
                            logging.debug("self.inputs length:{}".format(len(self.inputs)))
                            continue

                        # connection from software
                        elif not self.sock_dict["software"]:
                            if soc != self.sock_dict["controller"] and soc != self.sock_dict["device"]:
                                self.sock_dict["software"] = soc
                                logging.debug("connection from software")

                        # socket is ok!
                        if data != "": 
                            # data from controller, handle it.
                            if soc == self.sock_dict["controller"]:
                                #logging.debug("data from controller:{}".format(b2a_hex(data)))
                                self.handle_request_from_controller(data)
                            
                            # data from device
                            elif soc == self.sock_dict["device"]: 
                                logging.debug("data from device:{}".format(b2a_hex(data)))
                                self.socket_send(self.sock_dict["software"],data,"dirrect_to_software")
                    
                            # data from software, direct forward to device
                            else: 
                                logging.debug("data from software:{}".format(b2a_hex(data)))
                                # self.connect_to_target() # do not connect to target
                                self.recv_queue.append(data)
                        
                        # socket closed by peer
                        else: 
                            if soc in self.inputs:

                                self.inputs.remove(soc)

                            # controller offline
                            if soc == self.sock_dict["controller"]: 
                                logging.debug("socket_closed_by_peer:{}".format("controller offline!"))
                                self.sock_dict["controller"] = None
                                soc.close()

                            # device offline 
                            elif soc == self.sock_dict["device"]: 
                                logging.debug("socket_closed_by_peer:{}".format("device offline!"))
                                self.sock_dict["device"] = None
                                soc.close()
                                self.send_queue = []
                            
                            # software offline
                            elif soc == self.sock_dict["software"]:
                                logging.debug("socket_closed_by_peer:{}".format("software offline!"))
                                self.sock_dict["software"] = None
                                soc.close()
                                self.__clear_recv_queue() # software cache cleared
                                self.send_queue = [] # software send cache cleared
                                
                            
                            # unknow error happened
                            else:
                                logging.critical("unknow err happened,peer_name:{}".format(soc.getpeername()))
                                # sys.exit(0)
                                soc.close()
                                                
                for exp in exceps:
                    # maybe server?
                    logging.warning('Exception:{}'.format(exp.getpeername()))
                    if exp in self.inputs:
                        self.inputs.remove(exp)

            except Exception as error:
                logging.warning("Error info:{}".format(error))
                
                if soc in self.inputs:
                    self.inputs.remove(soc)

                errMsg = "{}".format(error)
                if errMsg.find("10054") >= 0:
                    if soc == self.sock_dict["software"]:
                        self.sock_dict["software"] = None
                        logging.warning("exp software offline")
                    if soc == self.sock_dict["device"]:
                        self.sock_dict["device"] = None
                        logging.warning("exp device offline")
                    if soc == self.sock_dict["controller"]:
                        self.sock_dict["controller"] = None
                        logging.warning("exp controller offline")                
 
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG) # can show debug info
    socket.setdefaulttimeout(30)

    ADDR = ("0.0.0.0",5007)
    
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(ADDR)
    server.listen(30)
    p = proxy(server)
    logging.debug("In logging level, proxy start")
    p.run()

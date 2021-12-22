import socket
import time
import json
import logging
from binascii import b2a_hex,a2b_hex
import subprocess
from struct import pack
import sys
import os
import threading
import random
import bisect
import collections
from utils import *

agent_ip = "10.10.2.151"
bitmap_proxy_ip = "10.10.2.151"
bitmap_proxy_port = 20012

agent_port = 10000
MUTATED_HEAD_LEN = 9
MUTATED_CONTENT_LEN = 13999

def get_mutated_data():
    logging.debug("in get_mutated_data")
    global agent_sock
    try:
        logging.debug("send @mutated completed!")
        agent_sock.send("@mutated:")
        # agent_sock.setdefaulttimeout(10)

        print("send ")
        recv = ""
        total_len = MUTATED_CONTENT_LEN + MUTATED_HEAD_LEN
        while len(recv) < total_len:
            recv += agent_sock.recv(total_len)
        return recv[9:]
    except Exception as e:
        logging.debug('error in get_mutated_data:{}'.format(e))
        if agent_sock is not None:
            agent_sock.close() 
        addr1 = (agent_ip,agent_port) # for agent
        agent_sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        agent_sock.connect(addr1)
        
        # agent_sock.setdefaulttimeout(2)
        logging.debug("reconnect to driver server!")
        agent_sock.send("@mutated:")
        recv = ""
        total_len = MUTATED_CONTENT_LEN + MUTATED_HEAD_LEN
        while len(recv) < total_len:
            recv += agent_sock.recv(total_len)
        return recv[9:]

def set_agent_bitmap(bitmap):
    global agent_sock
    the_bitmap = "@bitmap:{}".format(bitmap)
    # print(len())

    try:
        agent_sock.send(the_bitmap)

        return True
    except Exception as e:
        logging.debug('error in set_agent_bitmap:{}'.format(e))
        if agent_sock is not None:
            agent_sock.close() 
        addr1 = (agent_ip,agent_port) # for agent
        agent_sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        agent_sock.connect(addr1)
        agent_sock.setdefaulttimeout(10)
        logging.debug("reconnect to driver server!")
        agent_sock.send(the_bitmap)
        return True

def get_bitmap():
    global bitmap_proxy_sock
    logging.debug("get_bitmap")
    cmd = "bitmap"
    try:
        bitmap_proxy_sock.send(cmd)
        recv = ""
        while len(recv)<65537:
            recv += bitmap_proxy_sock.recv(65537)
        return recv
    except Exception as e:
        logging.debug("error in get_bitmap:{}".format(e))
        if bitmap_proxy_sock is not None:
            bitmap_proxy_sock.close()
        socket.setdefaulttimeout(2)
        addr = (bitmap_proxy_ip, bitmap_proxy_port) # for bitmap
        bitmap_proxy_sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        bitmap_proxy_sock.connect(addr)
        bitmap_proxy_sock.send(cmd)
        recv = ''
        while len(recv)!=65537:
            recv += bitmap_proxy_sock.recv(65537)
        return recv

def the_loop():
    # time.sleep(0.1)
    target_filename = "./pkts/business_1_reopen_1588086528.txt"
    tar_data_stream = load_data(target_filename)

    mutated = get_mutated_data()
    logging.debug(len(mutated))
    logging.debug("received:{}".format(b2a_hex(mutated[:9])))

    # mutated = mutated[9:]
    state, mutated = get_states(tar_data_stream, mutated)
    if len(mutated) == 0:
        mutated = '\x00'*5
    logging.debug("state:{}, mutated:{}, length:{}".format(state,b2a_hex(mutated[:10]), len(mutated)))
    # mutated = mutated.strip('\x00')
    # splited = mutated.split("[*****]") # split the packets according to states
    # count = 0
    # if len(splited) == 1: # total mutated, no split
    #     print(b2a_hex(splited[0][:50]))
    #     print("over")
    # else:
    #     for item in splited[:-1]:
    #         count += 1
    #         print(count, b2a_hex(item))
    #     print("over")
    # get_mutated_data()
    time.sleep(1)
    bitmap = get_bitmap()
    set_agent_bitmap(bitmap[1:])
    print("len(bitmap)",len(bitmap))

def get_states(data_stream, mutated):
    '''
    data_strem is the origin data_stream of inputs
    return: res_state, res_mutated
    '''
    res_state = 0
    res_mutated = None
    mutated = mutated.strip("\x00")
    logging.debug("striped len:{}".format(len(mutated)))
    splited = mutated.split("[*****]")
    logging.debug("splited len:{}".format(len(splited)))

    if len(splited) != 1:
        splited = splited[:-1]
    
    if len(splited) == 1:
        res_state = 0
        res_mutated = splited[0]
    else:
        length = len(splited)
        print(len(splited),len(data_stream))

        for i in range(0,length):
            if splited[i] == data_stream[i]:
                res_state += 1
            else:
                res_mutated = splited[i]
        # for item in splited:
        #     if data_stream.find(item)>=0:
        #         res_state += 1
        #     else:
        #         res_mutated = item
    if res_mutated is None: # there is no mutation
        res_mutated = splited[-1]
        
    return res_state, res_mutated


def init_agent():
    global agent_sock, bitmap_proxy_sock
    agent_sock = None
    bitmap_proxy_sock = None
    logging.basicConfig(level=logging.DEBUG)

def main():
    global agent_sock, bitmap_proxy_sock
    agent_sock = None
    bitmap_proxy_sock = None
    logging.basicConfig(level=logging.DEBUG)


if __name__ == '__main__':
    
    main()
    while True:
        the_loop()
    # main()

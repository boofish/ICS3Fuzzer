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


def check_stats(sock):
    sock.send("@stat:--")
    #logging.debug("sending stat cmd over...")
    time.sleep(0.01)
    recv = sock.recv(1024)
    logging.debug("stat:{}".format(recv))
    return json.loads(recv)

def forward_data(sock):
    sock.send("@fwrd:--")
    logging.debug("sending fwrd cmd over...")
    time.sleep(0.01)

def extract_recv_data(sock):
    sock.send("@recv:")
    #logging.debug("sending recv cmd over...")
    time.sleep(0.01)
    recv = sock.recv(1024)
    # logging.debug("recv:{}".format(b2a_hex(recv)))
    return recv

def modify_data(sock,data):
    sock.send("@mdfy:{}".format(data))
    # logging.debug("sending mdfy cmd over")
    time.sleep(0.01)

def fuzzing_start(sock):
    sock.send("@fuzz:--")
    #logging.debug("sending fuzz cmd over...")
    time.sleep(0.01)

def close_sock(sock):
    sock.send("@clos:--")
    time.sleep(0.01)

def cdf(weights):
    total = sum(weights)
    result = []
    cumsum = 0
    for w in weights:
        cumsum += w
        result.append(cumsum/total)
    return result

def choice(population, weights):
    assert len(population) == len(weights)
    cdf_vals = cdf(weights)
    x = random.random()
    idx = bisect.bisect(cdf_vals,x)
    return population[idx]

def select_one_state(state_dict):
    w = state_dict['weights']
    s = state_dict['state']
    return choice(s,w)

def load_data(filename):
    data_t = open(filename,'r').readlines()
    # print(filename)
    resp_data = []
    for item in data_t:
        # if item.find('server:') >= 0:
            # print([item.strip('\r\n')])
        if item.find('=') >= 0:
        	pass
        else:
        	resp_data.append(a2b_hex(item.strip('\r\n')))
    return resp_data


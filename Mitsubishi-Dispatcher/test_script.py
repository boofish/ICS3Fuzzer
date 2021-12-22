import os
import logging
from utils import load_data
from binascii import *
from struct import *

def re_arrange_pkts():
	base_dir = './pkts/'
	files = os.listdir(base_dir)
	for file in files:
		filename = base_dir + file
		data = open(filename,'rb').readlines()
		dataout = []
		for item in data:
			if item.find('=')<0:
				dataout.append(item.strip('\r\n'))
		fp = open(filename,'w')
		for item in dataout:
			fp.write(item+'\n')
		fp.close()

def encode(data): # complete constraint in datastream and between communication
	length = len(data)
	if length>=21:
		bin_data = pack('H',(length-21))
	else:
		bin_data = '\x00\x00'
	return data[:19]+bin_data+data[21:]

def main():
	logging.basicConfig(level=logging.DEBUG)
	filename = './pkts/read_from_plc.txt'
	lines = load_data(filename)
	for item in lines:
		logging.debug('origin:{}'.format(b2a_hex(item)))
		logging.debug('update:{}'.format(b2a_hex(encode(item))))


if __name__ == '__main__':
	main()
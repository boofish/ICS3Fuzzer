from binascii import *
from struct import *
import random

def maxk(arraylist,k): # max K element of a List
    maxlist=[]
    maxlist_id=range(0,k)
    m=[maxlist,maxlist_id]
    for i in maxlist_id:
        maxlist.append(arraylist[i])

    for i in range(k,len(arraylist)):
        if arraylist[i]>min(maxlist):
            mm=maxlist.index(min(maxlist))
            del m[0][mm]
            del m[1][mm]
            m[0].append(arraylist[i])
            m[1].append(i)
    return m


def load_data(filename):
    data_t = open(filename,'r').readlines()
    # resp_data = []
    the_dict = {}
    for item in data_t:
        data_item = a2b_hex(item.strip('\r\n'))
        the_dict[len(data_item)] = data_item
    return the_dict


def main():
	
	filename = './pkts/read_from_plc.txt'
	# filename = 'omoron.txt'
	# the_dict = read_pkt(filename)
	the_dict = load_data(filename)
	the_key = sorted(the_dict.keys())
	print('key count:',len(the_key))
	key_count = len(the_key)

	handle_dict = {}
	for key in the_key:
		item = the_dict[key]
		# item = a2b_hex(item)
		# print(item)
		content = []
		for byte in item:
			value = unpack('B',byte)[0]
			content.append(value-key)
		handle_dict[key] = content

	max_length = the_key[-1]
	offset = [0]*max_length

	for key in the_key:
		baseline = handle_dict[key] # every length packet can be a base
		for _,content in handle_dict.items():
			for i in range(0,max_length):
				try:
					if content[i] == baseline[i]:
						offset[i] += 1
				except Exception as e:
					# print(e)
					break

	ave_offset = [item/key_count for item in offset]
	# ave_offset = offset

	# maxlist,max_index = maxk(ave_offset,2)
	# print(maxlist,max_index)
	# print(max_index)
	maxlist,max_index = maxk(ave_offset,1)
	print('index=>',maxlist)
	print('max_index=>',max_index[0])
	print('relation:')
	for key in the_key:
		baseline = handle_dict[key]
		fixed_rel = baseline[max_index[0]]
		print('value=len+fixed;len:{},fixed:{}'.format(key,fixed_rel))

	
if __name__ == '__main__':
	main()
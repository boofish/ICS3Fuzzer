from binascii import *
from netzob.all import *
import json
import os
import re
# from cluster import *

	
def load_data(filename):
	data_lines = open(filename, 'rb').readlines()
	return [a2b_hex(item.strip('\r\n')) for item in data_lines]


def generate_json(base_dir, length, dataItem):
	datalist = dataItem[0][:300]
	datacnt = dataItem[1]

	outName = base_dir + 'Mitsubishi_field_{}.json'.format(length)

	fp = open(outName, 'w')
	result_dict = {}

	messages = [RawMessage(data=sample) for sample in datalist]
	symbol = Symbol(messages=messages)
	# Format.splitAligned(symbol,doInternalSlick=False)
	Format.splitStatic(symbol)
	
	idx_count = 0 
	for item in symbol.getCells():
		idx_count += 1
		# result_dict[idx_count] = b2a_hex(item)
		arr = []
		count = 0
		for field in item:
			if len(field) > 0:
				arr.append(b2a_hex(field))
		result_dict[idx_count] = arr
		if idx_count >= datacnt:
			break
	
	json_str = json.dumps(result_dict,indent=1)
	fp.write(json_str)
	fp.close()

def get_length(filenames):
	length_list = []
	for name in filenames:
		number = re.findall('\d+',name)[0]
		length_list.append(int(number))
	return length_list

def main():
	base_dir = './packets/'
	filenames = os.listdir(base_dir)
	len_list = sorted(get_length(filenames))
	data_dict = {}
	for i in range(0,len(len_list)):
		length = len_list[i]
		filename = base_dir + 'len_{}.txt'.format(length)
		data = load_data(filename)
		data_dict[length] = [data, len(data)] # second item is count of the data

		if len(data)<20:
			length_1 = len_list[i-1]
			filename_1 = base_dir + 'len_{}.txt'.format(length_1)
			data += load_data(filename_1)
			length_2 = len_list[i+1]
			filename_2 = base_dir + 'len_{}.txt'.format(length_2)
			data + load_data(filename_2)

	for k, v in data_dict.items():
		# base_dir, length, dataItem
		try:
			generate_json('./out/', k, v)
			print('Success of length {}'.format(k))
		except Exception as e:
			print('Attention: length of {} error!'.format(k))
		
if __name__ == '__main__':
	main()
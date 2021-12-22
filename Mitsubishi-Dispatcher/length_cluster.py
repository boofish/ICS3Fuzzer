import os
from state_filter import load_data
from binascii import b2a_hex

def main():
	length_dict = {}

	files = os.listdir('./pkts')

	for filename in files:
		fileItem = './pkts/'+filename
		lines = load_data(fileItem)
		for line in lines:
			length = len(line)
			# print(length)
			if length in length_dict.keys():
				length_dict[length].append(line)
			else:
				length_dict[length] = [line]
	
	length_list = sorted(list(length_dict.keys()))

	for i in length_list:
		filename = './length/len_{}.txt'.format(i)
		fp = open(filename, 'w')
		pkts = length_dict[i]
		for pkt in pkts:
			fp.write(b2a_hex(pkt)+'\n')
		fp.close()


	# print(files[0])

if __name__ == '__main__':
	main()
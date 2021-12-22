from binascii import *
import random
import bisect
import collections
import json

"""
State management and state selection.
an input state has three attributes, 
and we choose states according to (depth, #bb, data_richiness (length))
"""

def similar_pkt_pair(pkt1, pkt2):
	length = len(pkt1)
	same_cnt = 0
	for i in range(0,length):
		if pkt1[i] == pkt2[i]:
			same_cnt += 1
	t_ratio = (same_cnt  + 0.0)/length
	return t_ratio

def similar_bb_cnt_pair(bb_cnt1, bb_cnt2):
	diff = abs(bb_cnt1 - bb_cnt2)
	bb_cnt = max(bb_cnt1,bb_cnt2)
	t_ratio = (bb_cnt - diff + 0.0)/ bb_cnt

	return t_ratio

def load_data(filename):
    data_t = open(filename,'r').readlines()
    # print(filename)
    resp_data = []
    for item in data_t:
        if item.find('=') >= 0:
        	pass
        else:
        	resp_data.append(a2b_hex(item.strip('\r\n')))
    return resp_data

def load_bbcount(filename):
	data = open(filename,'r').readlines()
	bb_count = []
	for item in data:
		idx1= item.find('bb_count:')
		idx2 = item.find(',',idx1)
		count = item[idx1+9:idx2]
		bb_count.append(int(count,16))
	return bb_count

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

def gen_states(tracefile,pkt_file,out_file):
	global ratio

	filename = './trace/'+ tracefile
	bb_count = load_bbcount(filename)
	filename = './pkts/'+pkt_file
	pkts = load_data(filename)
	
	global history_dict, history_tuples, global_state_cnt, totoal_cnt
	state = []
	idx = 0
	item_cnt = len(bb_count)
	same_flag = False
	for i in range(0,item_cnt):
		cur_tuple = (pkts[i], bb_count[i])
		totoal_cnt += 1
		pkt_len = len(cur_tuple[0])
		try:
			his_tuples_list = history_tuples[pkt_len]
			for i_tuple in his_tuples_list:
				i_pkt = i_tuple[0]
				i_bbcnt = i_tuple[1]
				pkt_sim = similar_pkt_pair(cur_tuple[0],i_pkt) 
				bb_sim = similar_bb_cnt_pair(cur_tuple[1],i_bbcnt)
				if bb_sim*pkt_sim > ratio:
					# it is a similar tuple in history
					# print("they are same states")
					same_flag = True
					# print(b2a_hex(cur_tuple[0]))
					break
			# no similar in history
			if not same_flag:
				history_tuples[pkt_len].append(cur_tuple)
				global_state_cnt += 1
			else:
				same_flag = False
		except Exception as e:
			history_tuples[pkt_len] = [cur_tuple]
			# print(b2a_hex(cur_tuple[0]))
			global_state_cnt += 1

	for i in range(0,len(bb_count)):
		item = pkts[i]	   # packet
		length = len(item) # packet length
		bb_c = bb_count[i]

		if length in history_dict.keys():
			v = history_dict[length]
			if bb_c in v: # use 100% as 
				continue
			else: 
				v.append(bb_c)
				state.append(i)
		else:
			history_dict[length] = [bb_c]
			state.append(i)

	cnt = 0
	states = []
	baseline = [0,0,0]
	for s in state:
		cnt += 1
		attr = (bb_count[s],len(pkts[s]),cnt)
		states.append(attr)
		baseline[0]+=bb_count[s]
		baseline[1]+=len(pkts[s])
		baseline[2]+=cnt

	weights = []
	for st in states:
		w = (st[0]+0.0)/baseline[0] + (st[1]+0.0)/baseline[1] + (st[2]+0.0)/baseline[2]
		weights.append(w/3)
	# print(weights)
	s = 0
	for i in weights:
		s+=i
	# print("total weights:{}".format(s))
	population = state

	the_dict = {}
	the_dict['name'] = out_file[:-5]
	the_dict['state'] = state
	the_dict['weights'] = weights
	filename = out_file
	fp = open('./states/'+out_file,'w')
	fp.write(json.dumps(the_dict,indent=1))
	fp.close()
	return len(state)

def test_state_choice():
	the_dict = json.loads(open('./states/read_from_plc.json','r').read())
	w = the_dict['weights']
	s = the_dict['state']
	# for i in range(0,200):
	# 	state = choice(s,w)
	# 	print(state,type(state))
	counts = {}
	population = s
	weights = w

	for i in range(100000):
		try:
			counts[choice(population,weights)] += 1
		except:
			counts[choice(population,weights)] = 1

	print([(item+0.0)/sum(counts.values()) for item in counts.values()])

if __name__ == '__main__':
	test_state_choice()
	global history_dict, history_tuples, global_state_cnt, totoal_cnt,ratio
	history_dict = {}
	history_tuples = {}
	global_state_cnt = 0
	totoal_cnt = 0

	file_list = [('1.log_connect.txt','test_connect.txt','test_connect.json')]
	item = ('2.log_read_from_plc.txt', 'read_from_plc.txt','read_from_plc.json')
	file_list.append(item)
	item = ('3.log_write.txt','load_write.txt','load_write.json')
	file_list.append(item)
	item = ('4.log_title.txt','write_title.txt','write_title.json')
	file_list.append(item)

	state_cnt = 0
	ratio = 0.8
	for item in file_list:
		state_cnt += gen_states(item[0],item[1],item[2])
	# print("{}->state_cnt:{}".format(ratio,global_state_cnt))



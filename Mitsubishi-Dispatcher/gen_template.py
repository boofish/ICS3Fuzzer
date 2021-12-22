from binascii import *
import os
import json
import random

def is_str(field):
    for item in field:
        if ord(item)<0x7f and ord(item)>=0x20:
            continue
        else:
            return False
    return True

def generate_template(m_dict, fields, idx):
    t_arr = []
    for field in fields:
        if len(field)==0:
            continue
        if len(field)<=4:
            anno = ('number',b2a_hex(field))
            t_arr.append(anno)
        else:
            if is_str(field):
                anno = ('str',b2a_hex(field))
                t_arr.append(anno)
            elif len(field)==1:
                anno = ('binary',b2a_hex(field)) # not handle
                t_arr.append(anno)
            else:
                anno = ('binary',b2a_hex(field))
                t_arr.append(anno)
    m_dict[idx] = t_arr


def load_data(filename):
    lines = open(filename,'rb').readlines()
    return [a2b_hex(item.strip('\r\n')) for item in lines]


def load_rule(filename):
    t_dict = json.loads(open(filename,'r').read())
    return t_dict['1']

def dump_format(filename):
    print(filename)
    tag = filename[filename.rfind('/')+1:filename.rfind('_')]
    outfile = './template/{}.json'.format(tag)

    fp = open(outfile, 'w')

    dataList = load_data(filename)
    m_dict = {}

    idx = 0

    for item in dataList:
        length = len(item)

        rule_file_name = "./json/mitsubishi_field_{}.json".format(length)
        if os.path.exists(rule_file_name):
            rule = load_rule(rule_file_name)
        else:
            rule = None

        fields = []
        if rule is not None:
            start = 0
            for r in rule:
                field_len = len(r)/2
                end = start + field_len
                fields.append(item[start:end])
                start = end
            fields = rearrange_fields(fields)
            generate_template(m_dict,fields,idx)

            # print(b2a_hex(item[4]),len(item),len(fields),[b2a_hex(t) for t in fields])
            # print([b2a_hex(t) for t in fields])
        else:
            print(len(item),'no rule')
            generate_template(m_dict,[item],idx)
        idx += 1
    fp.write(json.dumps(m_dict,indent=1))
    fp.close()

def rearrange_fields(fields,min_len=5):
    ret = []
    for item in fields:
        ret += split_strings(item,min_len)
    return ret


def split_strings(s, min_len=5):
    result = []
    tmp = ''
    idx = 0
    for item in s:

        if ord(item)<0x7f and ord(item)>=0x20:
            tmp += item

        else:
            if len(tmp) >= min_len:
                result.append((idx,tmp))
                tmp = ''
                
            else:
                
                tmp = ''
        idx += 1
    if len(tmp) > min_len:
        result.append((idx,tmp))
    # print(result)
    ret = []
    next_idx = 0
    for item in result:
        idx = item[0]
        tmp_str = item[1]
        # if len(s[next_idx:idx-len(tmp_str)]) >0:
        ret.append(s[next_idx:idx-len(tmp_str)])
        ret.append(s[idx-len(tmp_str):idx])
        next_idx = idx
    remaing = s[next_idx:]
    if len(remaing)>0:
        ret.append(remaing)
    return ret


def main():
    the_dict = {}
    base_dir = './pkts/'
    filenames = os.listdir(base_dir)
    for file in filenames:
        fileItem = base_dir + file
        dump_format(fileItem)


if __name__ == '__main__':
    # genData()
    main()
    # filename = './pkts/read_from_plc.txt'
    # dump_format(filename)




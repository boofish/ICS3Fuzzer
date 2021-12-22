from utils import *
from mutate_engine import *
import json

# target_ip = "10.10.12.120"
target_ip = "192.168.227.130"
proxy_port = 5007
driver_port = 65534
watdog_port = 65533

STATE_BASE_DIR = "./states/"
TEMPLATE_BASE_DIR = "./template/"
LOG_DIR = "./logs/"
SESSION_FILE = "./logs/session.json"

his_mutate_state_dict = {} # for history record
mutate_state_dict = {} # for real-time mutate record

def load_last_session(filename,state_dict):
    t_his_mutate_state_dict = {}
    try:
        t_his_mutate_state_dict = json.loads(open(filename,'r').read())
    except Exception as e:
        for s in state_dict["state"]:
            t_his_mutate_state_dict[int(s)] = 0
        t_his_mutate_state_dict[-1] = 0
        t_his_mutate_state_dict[-2] = 0 # waste time cost
    
    # logging.debug(his_mutate_state_dict)
    # sys.exit(0)
    for k, v in t_his_mutate_state_dict.items():
        mutate_state_dict[int(k)] = 0
        his_mutate_state_dict[int(k)] = v
    return True


def shoud_feed(state):
    if (mutate_state_dict[state] +1) <= his_mutate_state_dict[state]:
        return False
    else:
        return True

def dump_session(filename):
    global msg_dict
    t_time_cost = time.time() - msg_dict["start"]

    
    time_cost = his_mutate_state_dict[-1] + t_time_cost
    time_waste = his_mutate_state_dict[-2] + mutate_state_dict[-2] 

    his_mutate_state_dict[-1] = time_cost # -1 for time cost
    his_mutate_state_dict[-2] = time_waste # -2 for time waste

    msg_dict["start"] = time.time()
    mutate_state_dict[-2] = 0

    for k,v in mutate_state_dict.items():
        if his_mutate_state_dict[k] < mutate_state_dict[k]:
            his_mutate_state_dict[k] = v

    fp = open(filename,'w')
    fp.write(json.dumps(his_mutate_state_dict,indent=1))
    fp.close()


def get_business_func_info(business_func_name):
    state_filename = STATE_BASE_DIR + business_func_name + '.json'
    state_dict = json.loads(open(state_filename, 'r').read())
    tmplate_filename = TEMPLATE_BASE_DIR + business_func_name + ".json"
    model = build_business_model(tmplate_filename)
    return state_dict, model

def launch_program():
    logging.debug("in enter_into_states function")
    execute_cmd("kill")
    logging.debug("kill command is delivered!")
    execute_cmd("launch")
    logging.debug("launch program")


def detect_crash():
    global record_number
    detect_cmd = "detect:{}".format(record_number)
    crash_status = execute_cmd(detect_cmd)
    logging.debug("crash_status:{}".format(crash_status))
    idx = crash_status.find(":")
    if idx >=0 :
        record_number = int(crash_status[idx+1:])
        crash_status = crash_status[:idx]

def feed_data_first_level(mutate_data, state, data_stream, cmd):
    logging.debug('in feed_data_first_level')
    start = time.time()
    global sock_dict, msg_dict, total_cnt, state_lib
    sock = sock_dict[proxy_port]
    feed_success = False

    time.sleep(1)
    execute_cmd(cmd)
    # time.sleep(4)
    launch_time = time.time() - start

    logging.debug("cmd:{} delivered, time_cost:{} ".format(cmd, launch_time))
   
    snd_idx = 0
    null_count = 0
    limited_cnt = 13
    check_flag = False
    
    logging.debug('================test state id:{}=========================='.format(state))

    while snd_idx < len(data_stream):
        logging.debug("before check_stats....")

        res_dict = wraped_send(check_stats, sock)

        logging.debug("after check_stats...")
        if res_dict["software"] == "off":
            logging.debug("software is off")

            null_count += 1

            time.sleep(0.01)

        if res_dict["software"] == "on" and res_dict["buf_cnt"] >=1:

            recv_data = extract_recv_data(sock)

            logging.debug("req->:{}".format(b2a_hex(recv_data)))

            if snd_idx == state:
                
                modify_data(sock, mutate_data)
                feed_success = True

                # logging.debug("communicate time:{}".format(time.time()-start))
                
                snd_idx += 1

                null_count = 0

                close_sock(sock)

                check_flag = True

                logging.debug("########## mutate_data has been send, and socket is closed ##########")

            else:

                if check_flag:
                    close_sock(sock)
                    logging.debug("#### re-close target socket ###")
                    null_count += 1

                else:
                    if snd_idx==0:
                        start = time.time()

                    # template should work here
                    modify_data(sock, data_stream[snd_idx])

                    logging.debug("rsp:{}->{}".format(snd_idx, b2a_hex(data_stream[snd_idx])))

                    snd_idx += 1
                    null_count = 0

        elif res_dict["buf_cnt"] == 0 and res_dict["software"] == "on":
            null_count += 1
            time.sleep(0.01)

        if check_flag:
            logging.debug("before detect!")
            global record_number
            detect_cmd = "detect:{}".format(record_number)
            crash_status = execute_cmd(detect_cmd)
            logging.debug("crash_status:{}".format(crash_status))
            idx = crash_status.find(":")
            if idx >=0 :
                record_number = int(crash_status[idx+1:])
                crash_status = crash_status[:idx]
            logging.debug("check cmd delivered!")

            if crash_status == "yes":
                logging.debug("crash detected!")
                execute_cmd("kill")
                state_lib.append(state)

                cmd_tag = cmd[cmd.find(':')+1:-4]
                crash_name = "crash_" + cmd_tag
                msg_dict["event"] = "crash detected!"
                msg_dict["state"] = state
                msg_dict["crash"] = mutate_data
                msg_dict["total_cnt"] = total_cnt
                log_generate(crash_name)
                
                break

        if null_count >= limited_cnt:
            logging.debug("Error: {} times no response!".format(null_count))
            break

    if feed_success:
        return True

    return False

def fuzzing_first_level(data_stream, business_func_name, cmd):
    global total_cnt, msg_dict, state_lib, state_dict, model

    msg_dict["function"] = business_func_name

    if state_dict is None:
        state_dict, model = get_business_func_info(business_func_name)

    count = 0
    choose_cnt = 0
    start_test = time.time()
    total_cnt = 0
    timeout_cnt = 0
    while True:
        try:
            state = choice(state_dict["state"], state_dict["weights"])

            # state = 7 # for test
            
            if len(state_lib) == len(state_dict["state"]):
                logging.debug("testcase is over iterated!")
                msg_dict["event"] = "testcase_is_over"
                msg_dict["total_cnt"] = total_cnt
                log_file = business_func_name + "_over"
                log_generate(log_file)
                break

            if state in state_lib:
                continue

            # state = 47 # for temp test
            choose_cnt += 1 # state count
            count = 0
            data_list = get_data_list(str(state), model[0], model[1])

            if len(data_list) == 0:
                
                state_lib.append(state)

                if len(state_lib) == len(state_dict["state"]):
                    msg_dict["event"] = "state: {} is over".format(state)
                    msg_dict["total_cnt"] = total_cnt
                    log_file = business_func_name + "_state"
                    log_generate(log_file)
                    break

            logging.debug("testcase state id ==> {}".format(state))

            real_cnt = 0

            while count < len(data_list):
                try:
                    # if state in state_lib: # 
                    #     continue
                
                    data = data_list[count]

                    if not shoud_feed(state):
                        count += 1
                        total_cnt += 1
                        mutate_state_dict[state] += 1
                        continue


                    t_time = time.time()

                    launch_program()   
                    
                    feed_state = feed_data_first_level(encode(data), state, data_stream, cmd)

                    if not feed_state:
                        waste_time = time.time() - t_time
                        mutate_state_dict[-2] += waste_time
                        continue

                    mutate_state_dict[state] += 1

                    timeout_cnt = 0
                    logging.debug("send count:{}, choose_cnt:{}".format(count, choose_cnt))
                    total_cnt += 1
                    logging.debug("testcase:{}, time_cost:{}".format(total_cnt,time.time()-msg_dict["start"]))
                    count += 1
                    real_cnt += 1
                
                except Exception as e:
                    logging.debug("err in fuzzing_first_level while loop:{}".format(e))
                    err = "{}".format(e)
                    if err.find("time") >= 0:
                        timeout_cnt += 1
                        logging.debug("timeout: send count:{}, choose_cnt:{}".format(count, choose_cnt))
                        if timeout_cnt >= 2:
                            init_target()
                            create_connection()
                            timeout_cnt = 0

                    if err.find("10061")>=0 or err.find("10054") >=0:
                        init_target()
                        create_connection()
                    else:
                        init_target()
                        create_connection()
            
            # dump_session(SESSION_FILE)
            if real_cnt >0 :
                dump_session(SESSION_FILE)

        except Exception as e:
            logging.debug('Error in fuzzing_first_level:{}'.format(e))
            logging.debug("total_cnt:{}".format(total_cnt))

            init_target()
            create_connection()

def init_target():
    logging.debug("in init_target")
    global sock_dict
    try:
        sock = sock_dict[watdog_port]
        sock.send("reset")
        logging.debug("reset command is dirrectly delivered!")
        time.sleep(1)
        dump_session(SESSION_FILE) # backup the log

    except Exception as e:
        logging.debug("in init_target:{}".format(e))
        addr1 = (target_ip, watdog_port) # for reset environment
        sock1 = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        sock1.connect(addr1)
        sock1.send("reset")
        time.sleep(1)
        logging.debug("reset command is delivered!")
        sock_dict[watdog_port] = sock1

def create_connection():
    timeout = 8
    socket.setdefaulttimeout(timeout)

    global sock_dict
    try:
        if watdog_port in sock_dict.keys():
            sock_dict[watdog_port].close()

    except Exception as e:
        logging.debug('watdog_port->in create_connection :{}'.format(e))

    try:
        if proxy_port in sock_dict.keys():
            sock_dict[proxy_port].close()
    except Exception as e:
        logging.debug('5007->in create_connection :{}'.format(e))
    

    try:
        if driver_port in sock_dict.keys():
            sock_dict[driver_port].close()
    except Exception as e:
        logging.debug('65534->in create_connection :{}'.format(e))
    
    addr1 = (target_ip,watdog_port) # for reset environment
    sock1 = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    sock1.connect(addr1)
    sock_dict[watdog_port] = sock1
    

    addr2 = (target_ip,proxy_port) # for proxy
    sock2 = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    sock2.connect(addr2)
    sock2.send("iamcontroller")
    time.sleep(0.01)
    sock_dict[proxy_port] = sock2
    
    addr3 = (target_ip,driver_port) # for driver server
    sock3 = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    sock3.connect(addr3)
    sock_dict[driver_port] = sock3

    return sock_dict

def wraped_send(func_ptr,sock):
    global sock_dict
    try:
        res = func_ptr(sock)
        return res
    except Exception as e:
        logging.debug("error in wraped_send:{}".format(e))
        sock.close()
        socket.setdefaulttimeout(4)
        addr1 = (target_ip,proxy_port) 
        sock1 = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        sock1.connect(addr1)
        logging.debug("reconnect in wraped_send")
        sock1.send("iamcontroller")
        time.sleep(0.01)
        recv = func_ptr(sock1)
        logging.debug("send command over!")
        sock_dict[proxy_port] = sock1
        return recv

def execute_cmd(cmd):
    global sock_dict
    try:
        sock = sock_dict[driver_port]
        sock.send(cmd)
        recv = sock.recv(1024)
        return recv
    except Exception as e:
        logging.debug('error in execute_cmd:{}'.format(e))
        sock.close()
        socket.setdefaulttimeout(2)
        addr1 = (target_ip,driver_port) # for driver
        sock1 = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        sock1.connect(addr1)
        logging.debug("reconnect to driver server!")
        sock1.send(cmd)
        recv = sock1.recv(1024)
        logging.debug("send cmd over!")
        sock_dict[driver_port] = sock1
        return recv

# filename is a prefix
def log_generate(filename):
    global msg_dict
    
    log_file = LOG_DIR + filename + '_' + str(time.time())[:10]+'.txt'
    fp = open(log_file,'w')

    msg = msg_dict["function"] + "\r\n"
    if msg_dict["crash"] is not None:
        msg += "state:{}\r\n".format(msg_dict["state"])
        msg += "{}\r\n".format(b2a_hex(msg_dict["crash"]))
    cur_time = time.time()
    msg += "time_cost:{}\r\n".format(cur_time-msg_dict["start"])
    msg += "total_cnt:{}\r\n".format(msg_dict["total_cnt"])
    msg += "event:{}\r\n".format(msg_dict["event"])

    msg_dict["state"] = None
    msg_dict["crash"] = None
    msg_dict["event"] = ""

    fp.write(msg)
    fp.close()


def main():
    logging.basicConfig(level=logging.DEBUG)

    business_func_name = "read_from_plc"

    global state_dict, model
    state_dict = None
    model = None
    state_dict, model = get_business_func_info(business_func_name)

    if not load_last_session(SESSION_FILE, state_dict): # 
        for s in state_dict["state"]:
            his_mutate_state_dict[int(s)] = 0
            mutate_state_dict[int(s)] = 0
    # dump_session("./logs/session.json")
    # sys.exit(0)

        # his_mutate_state_dict

    global state_lib
    state_lib = []

    global sock_dict, total_cnt
    sock_dict = {}
    total_cnt = 0

    global msg_dict
    msg_dict = {}
    msg_dict["total_cnt"] = 0 # test_case count
    msg_dict["function"] = business_func_name # should adjust
    msg_dict["start"] = time.time()
    msg_dict["crash"] = None # should adjust
    msg_dict["state"] = None # should adjust
    msg_dict["event"] = "" # should adjust


    # start = time.time()
    # init_target()
    # create_connection()

    # detect_crash() # update record_number

    # target_filename = "./pkts/test_connect.txt"
    target_filename = "./pkts/read_from_plc.txt"
    tar_data_stream = load_data(target_filename)

    while True:
        try:
            # fuzzing_first_level(tar_data_stream,"test_connect", "operation:mit_connect_test.exe")
            init_target()
            create_connection()
            detect_crash() # update record_number
            fuzzing_first_level(tar_data_stream, business_func_name, "operation:mit_read_from_plc.exe")
        except Exception as e:
            logging.debug("error in main: {}".format(e))
            global record_number
            log_file = "test_connect" # it is a prefix
            msg_dict["total_cnt"] = total_cnt
            msg_dict["function"] = "test_connect"
            msg_dict["event"] = "fuzzing_first_level_over"
            log_generate(log_file)
        dump_session(SESSION_FILE)
        time.sleep(200)
        # global msg_dict
        msg_dict["start"] = time.time()
        mutate_state_dict[-2] = 0 #time waste 
        log_generate("main_loop_exit")


if __name__ == "__main__":
    # bcdedit /set IncreaseUserVA 2800
    global record_number
    record_number = 37827
    while True:
        try:
            main()
        except Exception as e:
            dump_session(SESSION_FILE)
            time.sleep(200)
            global msg_dict
            msg_dict["start"] = time.time()
            mutate_state_dict[-2] = 0 #time waste 



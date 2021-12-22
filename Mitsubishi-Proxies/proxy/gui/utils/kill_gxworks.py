import os
import subprocess

def get_pid(s):
	if len(s) == 0:
		return None
	idx = s.find(' ')
	start = end = 0
	for i in range(idx,len(s)):
		if s[i]!=' ':
			start = i
			break
	end = s.find(' ',start)
	return s[start:end]

def kill_drrun():
	cmd = "tasklist|findstr execute_drrun.exe*"
	proc = subprocess.Popen(cmd,shell=True,stdin=subprocess.PIPE,stdout=subprocess.PIPE)
	output = proc.communicate()[0]
	target_pid = get_pid(output)
	print("execute_drrun.exe pid:{}".format(target_pid))
	if target_pid is not None:
		cmd = "taskkill /PID {} /F".format(target_pid)
		os.system(cmd)
		print('killed the target_pid')


def main():
	kill_drrun()
	cmd = "tasklist|findstr dw20.exe*"
	proc = subprocess.Popen(cmd,shell=True,stdin=subprocess.PIPE,stdout=subprocess.PIPE)
	output = proc.communicate()[0]
	target_pid = get_pid(output)
	print("dw20.exe pid:{}".format(target_pid))
	if target_pid is not None:
		cmd = "taskkill /PID {} /F".format(target_pid)
		os.system(cmd)
		print('killed the target_pid')

	cmd = "tasklist|findstr WerFault.exe*"
	proc = subprocess.Popen(cmd,shell=True,stdin=subprocess.PIPE,stdout=subprocess.PIPE)
	output = proc.communicate()[0]
	target_pid = get_pid(output)
	print("WerFault.exe pid:{}".format(target_pid))
	if target_pid is not None:
		cmd = "taskkill /PID {} /F".format(target_pid)
		os.system(cmd)
		print('killed the target_pid')

	cmd = "tasklist|findstr GD2*"
	proc = subprocess.Popen(cmd,shell=True,stdin=subprocess.PIPE,stdout=subprocess.PIPE)
	output = proc.communicate()[0]
	target_pid = get_pid(output)
	print("GD2.exe pid:{}".format(target_pid))
	if target_pid is not None:
		cmd = "taskkill /PID {} /F".format(target_pid)
		os.system(cmd)
		print('killed the target_pid')
	# print([get_pid(output)])
	cmd = "tasklist|findstr ECMonitor*"
	proc = subprocess.Popen(cmd,shell=True,stdin=subprocess.PIPE,stdout=subprocess.PIPE)
	output = proc.communicate()[0]
	target_pid = get_pid(output)
	print("ECMonitor* pid:{}".format(target_pid))
	if target_pid is not None:
		cmd = "taskkill /PID {} /F".format(target_pid)
		os.system(cmd)
		print('killed the target_pid')
	
	# os.system("tasklist|findstr FrameworkX")

if __name__ == '__main__':
	main()
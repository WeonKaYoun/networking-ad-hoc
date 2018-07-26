from paramiko import SSHClient, AutoAddPolicy
import os, sys

MINE = 1
ipAddress = []
INFO_PATH = '/home/pi/info.txt'
IS_MANAGER = 0

def connectToPi(ip, username='pi', pw='1357') :
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())
    ssh.connect(ip,username=username,password=pw)
    return ssh

def sendCommand(ssh, command, pw='1357') :
    stdin, stdout, stderr = ssh.exec_command(command)
    if "sudo" in command :
        stdin.write(pw+'\n')
    stdin.flush()

def routeInitial(myssh, text) :
    info_path = INFO_PATH.split("/home/pi/")
    cmd = "vi -c \"%s/initail/"+text+"/g\" -c \"wq\" " + info_path[1]+"" # step 3-1 : write txt file in neibor node
    sendCommand(myssh, command=cmd)
    cmd = "python middle_node_start.py"
    sendCommand(myssh, command=cmd) # step 3-2 : run middle_node_start.py to route input to neighbor's neighbor
    
def adHocNetwork(dest, text) :
    myssh = connectToPi(ip=dest)
    routeInitial(myssh, text)
    
def isManager(managerList) :
    managers = managerList.split(" ")
    for i in range(0, length(managers)) :
        if(int(managers[i]) == MINE) return '1'
    return '0'

## code starts ##
myIpIndex = 0
numOfNode = input()
startNodeId = input()

text = numOfNode + "\n" + startNodeId

for i in range(0, int(numOfNode)) :
    tempIp = input()
    ipAddress.append(tempIp)
    text += "\n" + tempIp # step 1 : get users input
    
# get manager node's id until user click enter ******
managerList = input()
IS_MANAGER = isManager(managerList)

f = open(INFO_PATH,'w+')
f.write(text) # step 2 : write inputs in file in its node
f.close()

adHocNetwork(ipAddress[1], text) # step 3 : route inputs to other nodes

cmd = "python main.py " + IS_MANAGER # step 4 : start main.py
os.system(cmd)
print("done")
from paramiko import SSHClient, AutoAddPolicy
import os, sys

MINE = 1
ipAddress = []
INFO_PATH = '/home/pi/info.txt'

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

## code starts ##
myIpIndex = 0
numOfNode = input()
startNodeId = input()

f = open(INFO_PATH,'w+')
text = numOfNode + "\n" + startNodeId

for i in range(0, int(numOfNode)) :
    tempIp = input()
    ipAddress.append(tempIp)
    text += "\n" + tempIp # step 1 : get users input
    
f.write(text) # step 2 : write inputs in file in its node
f.close()

adHocNetwork(ipAddress[MINE], text) # step 3 : route inputs to other nodes

cmd = "python main.py" # step 4 : start main.py
os.system(cmd)
print("done")
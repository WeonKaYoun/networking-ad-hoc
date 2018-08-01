from paramiko import SSHClient, AutoAddPolicy
import os, sys

MINE = 2
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
    #cmd = "vi -c \"%s/initail/"+text+"/g\" -c \"wq\" " + info_path[1]+"" # step 3-1 : write txt file in neibor node
    cmd = "for i in $(seq 1); do echo " + text + ">> " + info_path[1] + "; done"
    sendCommand(myssh, command=cmd)
    cmd = "python middle_node.py"
    sendCommand(myssh, command=cmd) # step 3-2 : run middle_node_start.py to route input to neighbor's neighbor
    
def adHocNetwork(dest, text) :
    myssh = connectToPi(ip=dest)
    routeInitial(myssh, text)

## code starts ##
f = open(INFO_PATH,'r')
numOfNode = f.readline()

startNodeId = f.readline()
#text = numOfNode + "\n" + startNodeId
text = "\"" + numOfNode + startNodeId
for i in range(0, int(numOfNode)) :
    tempIp = f.readline()
    ipAddress.append(tempIp)
    text = text + tempIp
    if int(tempIp[10:]) == MINE :
        myIpIndex = i

managerList = f.readline()
#text += "\n" + managerList
text = text + managerList +"\""
f.close()

if myIpIndex != (int(numOfNode)-1) :
    adHocNetwork(ipAddress[myIpIndex+1], text) # step 3 : route inputs to other nodes

cmd = "python3 main.py" # step 4 : start main.py
os.system(cmd)
print("done")

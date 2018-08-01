from paramiko import SSHClient, AutoAddPolicy
import os, sys
from threading import Thread, Condition

MINE = 1
ipAddress = []
INFO_PATH = '/home/pi/info.txt'
IS_MANAGER = '0'

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
    #cmd = "vi -c \"%s/initial/"+text+"/g\" -c \"wq\" " + info_path[1]+"" # step 3-1 : write txt file in neibor node
    cmd = "for i in $(seq 1); do echo " + text + ">> " + info_path[1] + "; done"
    sendCommand(myssh, command=cmd)
    print("start other")
    cmd = "python middle_node_start.py"
    #cmd = "python main.py" # for test
    sendCommand(myssh, command=cmd) # step 3-2 : run middle_node_start.py to route input to neighbor's neighbor
    #startOtherNodeThread = StartOtherNodeThread()
    #thread = threading.Thread(target=startOtherNodeThread.run)
    #thread.start()
    
def adHocNetwork(dest, text) :
    myssh = connectToPi(ip=dest)
    print(myssh)
    routeInitial(myssh, text)
    
def isManager(managerList) :
    managers = managerList.split(" ")
    for i in range(0, len(managers)) :
        if(int(managers[i]) == MINE):
            return '1'
    return '0'

## code starts ##
myIpIndex = 0
numOfNode = input()
startNodeId = input()

#text = numOfNode + "\n" + startNodeId
text = "\"" + numOfNode + "\n" + startNodeId

for i in range(0, int(numOfNode)) :
    tempIp = input()
    ipAddress.append(tempIp)
    text += "\n" + tempIp # step 1 : get users input
    
# get manager node's id until user click enter
managerList = input()
text +="\n" + managerList +"\""
print("manager list : " + managerList)
IS_MANAGER = isManager(managerList)
print("IS_MANAGER : " + IS_MANAGER)

cmd = "for i in $(seq 1); do echo " + text + ">> " + INFO_PATH + "; done"
os.system(cmd)

adHocNetwork(ipAddress[1], text) # step 3 : route inputs to other nodes

cmd = "python main.py" # step 4 : start main.py
#cmd = "python pyaudioPlayer.py" # for test
os.system(cmd)
print("program done")
from paramiko import SSHClient, AutoAddPolicy

ipAddress = []
  
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

# routing detection to destNode
# write [MINE] + from + [srcNode] in detect.txt
def routeInitial(myssh, numOfNode) :
    replaceStr = numOfNode+"\n"+numOfNode-1
    for i in range(0, int(numOfNode)) :
        replaceStr += "\n"+ipAddress[i]
    cmd = "vi -c \"%s/initail/"+replaceStr+"/g\" -c \"wq\" " + ipAddress[1]+""
    sendCommand(myssh, command=cmd)
    
# check detection recursively
# if line is "node" -> no detection
# else detection -> route detection to neighbor node
# nodes[0] : neighbor node
# nodes[1] : source node
def adHocNetwork(dest, src) :
    myssh = connectToPi(ip=ipAddress[1])
    routeInitial(myssh, numOfNode)
    #time.sleep(random.random())

numOfNode = raw_input() # get number of nodes in this side
for i in range(0, int(numOfNode)) :
    tempIp = raw_input()
    ipAddress.append(tempIp)

# 1. should login to ipAddress[1] > adHocNetwork // did it
# 2. should write text file that include ipAddresses, loc of this Node etc // in manager_start.py
# 3. should apply this on main.py // read the text file and initialize variables
from paramiko import SSHClient, AutoAddPolicy

#process 3
NO_DETECTION = "node"
INPUT_FILE = "/home/pi/detect.txt"
#second node side
MINE = "2"
ROUTING_TABLE = {'1':'3', '3':'1'}
IP_TABLE = {'1':'192.168.1.1', '3':'192.168.1.3'}

def connectToPi(ip, userName='pi', pw='1357') :
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())
    ssh.connect(ip, username=userName, password =pw)
    print('connection status = ', ssh.get_transport().is_active())
    return ssh

def sendCommand(ssh, command, pw='1357') :
    print('sending a command . . . ', command)
    stdin, stdout, stderr = ssh.exec_command(command)
    if "sudo" in command :
        stdin.write(pw+'\n')
    stdin.flush()
    print('\nstdout : ',stdout.read())
    print('\nstderr : ',stderr.read())

# routing detection to destNode
# write [MINE] + from + [srcNode] in detect.txt
def routeDetection(myssh, srcNode) :
    replaceStr = MINE + "from" +srcNode
    cmd = "vim -c \"%s/node/"+replaceStr+"/g\" -c \"wq\" detect.txt"
    sendCommand(myssh, command=cmd)
    
# check detection recursively
# if line is "node" -> no detection
# else detection -> route detection to neighbor node
# nodes[0] : neighbor node
# nodes[1] : source node
def checkDetection() :
    f = open(INPUT_FILE,'r+')
    line = f.readline()
    if line == NO_DETECTION :
        f.close()
    else :
        nodes = line.split("from")
        destPi = ROUTING_TABLE[nodes[0]]
        myssh = connectToPi(ip=IP_TABLE[destPi])
        routeDetection(myssh, nodes[1])
        f.write(NO_DETECTION)
        f.close()
    #checkDetection()

checkDetection()
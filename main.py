from paramiko import SSHClient, AutoAddPolicy

#process 3
NO_DETECTION = "node"
INPUT_FILE = "/home/pi/detect.txt"

#third node side
MINE = "3"
ROUTING_TABLE = {'1':2, '2':1}
IP_TABLE = {1:'192.168.1.1', 2:'192.168.1.2'}

def connectToPi(ip, username='pi', pw='1357') :
    print('connecting to {}@{}...'.format(username,ip))
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())
    ssh.connect(ip,username=username,password=pw)
    print('connection status = ',ssh.get_transport().is_active())
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
    cmd = "vi -c \"%s/node/"+replaceStr+"/g\" -c \"wq\" detect.txt"
    sendCommand(myssh, command=cmd)
    
# check detection recursively
# if line is "node" -> no detection
# else detection -> route detection to neighbor node
# nodes[0] : neighbor node
# nodes[1] : source node
def checkDetection() :
    f = open(INPUT_FILE,'r')
    line = f.readline()
    if line == NO_DETECTION :
        f.close()
    else :
        nodes = line.split("from")
        f.close()
        destPi = ROUTING_TABLE[nodes[0]]
        myssh = connectToPi(ip=IP_TABLE[destPi])
        routeDetection(myssh, nodes[1])
        f = open(INPUT_FILE,'w+')
        f.write(NO_DETECTION)
        f.close()
    #checkDetection()

checkDetection()
#myssh = connectToPi(ip='192.168.1.1')
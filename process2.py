#import pyaudio
#import wave
#import sys
import random
from paramiko import SSHClient, AutoAddPolicy

MINE = '1'
ROUTE_PATH = '192.168.1.2'

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

def routeDetection(myssh) :
    replaceStr = MINE + "from" +MINE
    cmd = "vim -c \"%s/node/"+replaceStr+"/g\" -c \"wq\" detect.txt"
    sendCommand(myssh, command=cmd)

def isDanger() :
    randNum = random.randrange(0,2)
    # if danger > 1
    # else 0
    return randNum

def checkWav() :
    check = isDanger()
    print(check)
    if check == 1 :
        # should route danger to neighbor node
        myssh = connectToPi(ip=ROUTE_PATH)
        routeDetection(myssh)

checkWav()
        
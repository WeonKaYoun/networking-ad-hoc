from paramiko import SSHClient, AutoAddPolicy
import random
import pyaudio
import wave
from threading import Thread, Condition
import RPi.GPIO as GPIO
import time
import os, sys

def sendCommand(ssh, command, pw='1357') :
    #print('sending a command . . . ', command)
    stdin, stdout, stderr = ssh.exec_command(command)
    if "sudo" in command :
        stdin.write(pw+'\n')
    stdin.flush()
    
replaceStr = "\"this is"+"\n"+"daeun\""
input_file = "info.txt"
#cmd = "vi -c \"%s/node/"+replaceStr+"/g\" -c \"wq\" " + input_file[1] +""
cmd = "for i in $(seq 1); do echo " + replaceStr + ">> " + input_file + "; done"
print(cmd)
os.system(cmd)





from paramiko import SSHClient, AutoAddPolicy
import random
import pyaudio
import wave
from threading import Thread, Condition
import RPi.GPIO as GPIO
import time
import paramiko
import sys

MINE = 3
num_of_nodes = 0
txt = ""
next_node = 0
pre_node = 0

def connectToPi(ip, username='pi', pw='1357') :
    print('connecting to {}@{}...'.format(username,ip))
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())
    ssh.connect(ip,username=username,password=pw)
    print('connection status = ',ssh.get_transport().is_active())
    return ssh

def sendCommand(ssh, command, pw='1357') :
    stdin, stdout, stderr = ssh.exec_command(command)
    if "sudo" in command :
        stdin.write(pw+'\n')
    stdin.flush()
    
def routeFile(myssh, txt) :
    info_path = "tempfile.txt"
    cmd1 = "rm "+ info_path
    sendCommand(myssh, command=cmd1)
    cmd = "for i in $(seq 1) ; do echo " + "\""+txt + "\""+">> " + info_path + "; done"
    sendCommand(myssh, command=cmd)
   

def adhocNetwork(dest, txt) :
    myssh = connectToPi(ip=dest)
    routeFile(myssh, txt)
    
#write new file
def changeInfo(ip) :
    global num_of_nodes
    global txt
    
    num_of_nodes = num_of_nodes-1
   
    f = open('info.txt','r')
    line = f.readline()
    lines=f.readlines()
    f.close()
            
    f = open('info2.txt','w')
    f.write(str(num_of_nodes)+'\n')
    txt = str(num_of_nodes) + "\n"
    for i in lines :
        if i != ip :
            f.write(i)
            txt += i
    
def start() :
    global num_of_nodes
    global next_node
    global pre_node
    
    f = open('info.txt','r')
    
    # save num of nodes, start of nodes Id
    num_of_nodes = f.readline()
    start_of_nodeId = f.readline()
    num_of_nodes = int(num_of_nodes)
    start_of_nodeId = int(start_of_nodeId)
    
    # save IP addresses
    ip_list = [None]*(num_of_nodes)
    node_list = [None]*(num_of_nodes)
    
    for i in range(0,num_of_nodes):
        ip_list[i] = f.readline()
        node_list[i] = int(ip_list[i][10:])

    mid = (node_list[0]+node_list[num_of_nodes-1])/2
    f.close()
    
    # set couple_left , couple_right
    couple_left = 0
    couple_right = 999999
    
    for i in range(0, num_of_nodes):
        if(node_list[i] < mid and couple_left < node_list[i]):
            couple_left = node_list[i]
            left_idx = i
        elif(node_list[i] > mid and couple_right > node_list[i]):
            couple_right = node_list[i]
            right_idx = i
        
    print("left", couple_left)
    print("right", couple_right)
    print("left idx", left_idx)
    print("right idx", right_idx)

    isSSHworks = -1
    #sys.exit(1)

    if(MINE == couple_left):
        try:
            myssh = connectToPi(ip=ip_list[right_idx])
            isSSHworks=1
            print("ssh success : ",ip_list[right_idx])
        except paramiko.ssh_exception.NoValidConnectionsError:
            isSSHworks=0
            print("ssh fail")
    elif(MINE == couple_right):
        try:
            myssh = connectToPi(ip=ip_list[left_idx])
            isSSHworks=1
            print("ssh success : ",ip_list[left_idx])
        except paramiko.ssh_exception.NoValidConnectionsError:
            isSSHworks=0
            print("ssh fail")
        
    if(isSSHworks == 0) : #couple is dead
        if MINE == couple_left : #when right side is dead (here, node 4)
            changeInfo(ip_list[right_idx]) #write new file
            next_node = ip_list[right_idx+1]
            pre_node = ip_list[left_idx-1]

        elif MINE == couple_right : 
            changeInfo(ip_list[right_idx]) #write new file
            next_node = ip_list[right_idx+1]
            pre_node = ip_list[left_idx-1]
        
start()
adhocNetwork(next_node, txt) #send file to next node
adhocNetwork(pre_node, txt) #send file to previous node
#temp="192.168.1.2"
#adhocNetwork(temp,txt)
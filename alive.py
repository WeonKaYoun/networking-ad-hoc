from paramiko import SSHClient, AutoAddPolicy
import random
import pyaudio
import wave
from threading import Thread, Condition
import RPi.GPIO as GPIO
import time

MINE=5
def connectToPi(ip, username='pi', pw='1357') :
    print('connecting to {}@{}...'.format(username,ip))
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())
    ssh.connect(ip,username=username,password=pw)
    print('connection status = ',ssh.get_transport().is_active())
    return ssh


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
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        
if(MINE == couple_left):
    myssh = connectToPi(ip=ip_list[right_idx])
elif(MINE == couple_right):
    myssh = connectToPi(ip=ip_list[left_idx])


from paramiko import SSHClient, AutoAddPolicy
import paramiko
import random
import pyaudio
import wave
import threading
from threading import Thread, Condition
import time
import sys
import RPi.GPIO as GPIO
import os, sys
import subprocess as sp
from scipy.io import wavfile
from tfModelCNN import *

GPIO.setmode(GPIO.BCM)
GPIO.setup(23, GPIO.OUT)
GPIO.setup(24, GPIO.OUT)

INFO_FILE = 'info.txt'

NO_DETECTION = "node"
INPUT_FILE = ["/home/pi/detect1.txt", "/home/pi/detect2.txt", "/home/pi/detect3.txt", "/home/pi/detect4.txt",
              "/home/pi/detect5.txt"]
NUM_OF_FILE = 5
TARGET_MINE = 0
TARGET_OTHER = 0
IS_MANAGER = 0

# var for part 1 starts
CHUNK = 8192
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
RECORD_SECONDS = 0.2

p = pyaudio.PyAudio()

stream = p.open(format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK,input_device_index=0, output_device_index =0)

MAX_NUM = 10
queue = [None] * MAX_NUM
condition_queue = Condition()
condition_adhoc = Condition()
condition_detect = Condition()
in_queue = 0
out_queue = 0
count = 0
isWork = 0
# var for part 1 ends

# first node side
MINE ="3"
#ROUTING_TABLE = {'3': 2, '2': 3}
ROUTE_PATH = ''
# IP_TABLE = {3: '192.168.1.3', 2: '192.168.1.2'}

num_of_nodes = 6
start_of_nodeId = 0  # add ittttt
txt = ""
next_node = 0
pre_node = 0
# ip_list = [None] * (num_of_nodes)
# node_list = [None] * (num_of_nodes)
# ip_list = []
node_list = []
couple_left = 0
couple_right = 0
left_idx = -1
right_idx =0
my_idx = 0
managers = []
managerList = ""
mid = 0

ALERT_TABLE = {}  # NODE : IS_DETECTED // !!! should change this !!!
# numOfNode = 3
condition_alert = Condition()


def connectToPi(ip, username='pi', pw='1357'):
    print('connecting to {}@{}...'.format(username,ip))
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())
    ssh.connect(ip, username=username, password=pw)
    return ssh


def sendCommand(ssh, command, pw='1357'):
    stdin, stdout, stderr = ssh.exec_command(command)
    if "sudo" in command:
        stdin.write(pw + '\n')
    stdin.flush()
    # print('\nstdout : ',stdout.read())
    # print('\nstderr : ',stderr.read())


# routing detection to destNode
# write [MINE] + from + [srcNode] in detect.txt
def routeDetection(myssh, srcNode):
    global TARGET_OTHER
    replaceStr = MINE + "from" + srcNode
    input_file = INPUT_FILE[TARGET_OTHER].split("/home/pi/")
    cmd = "vi -c \"%s/node/" + replaceStr + "/g\" -c \"wq\" " + input_file[1] + ""
    #print("JUST WROTE" + replaceStr + "IT'S TARGET WAS " + str(TARGET_OTHER))
    TARGET_OTHER = (TARGET_OTHER + 1) % NUM_OF_FILE
    sendCommand(myssh, command=cmd)


def routeFile(myssh, txt):
    info_path = "info.txt"
    cmd1 = "rm " + info_path
    sendCommand(myssh, command=cmd1)
    cmd = "for i in $(seq 1) ; do echo " + "\"" + txt + "\"" + ">> " + info_path + "; done"
    sendCommand(myssh, command=cmd)


# check detection recursively
# if line is "node" -> no detection
# else detection -> route detection to neighbor node
# nodes[0] : neighbor node
# nodes[1] : source node
# write new filech
def changeInfo(ip):
    global num_of_nodes
    global txt
    global managerList
    global start_of_nodeId

    num_of_nodes = num_of_nodes - 1
    
    while True:
        try:
            f = open('info.txt', 'r')
            break
        except FileNotFoundError:
            print("info.txt File Not Found Error ! I try again!")
       
    
    #f = open('info.txt', 'r')
    line = f.readline()
    trash = f.readline()
    lines = f.readlines()
    f.close()
    
    while True:
        try:
            f = open('info.txt', 'w')
            break
        except FileNotFoundError:
            print("info.txt File Not Found Error ! I try again!")
        
    #f = open('info.txt', 'w')
    f.write(str(num_of_nodes) + '\n')
    f.write(str(start_of_nodeId) + '\n')
    txt = str(num_of_nodes) + "\n" + str(start_of_nodeId) + "\n"
    for i in range(0,int(line)):
        if lines[i] != ip:
            f.write(lines[i])
            txt += lines[i]
    f.write(managerList)
    txt += managerList

def adHocNetwork(dest, src):
    condition_adhoc.acquire()
    ip=dest
    cnt = 0
    while True:
        status,result = sp.getstatusoutput("ping -c1 -w2 " + ip)
    
        if(status != 0 and cnt >2):
            cnt = 0
            changeInfo(ip)
            print("system " + ip + " is DOWN !")
            break
        elif(status != 0):
            cnt = cnt + 1
        else :
            myssh = connectToPi(ip=dest)
            routeDetection(myssh, src)
            myssh.close()
            print("system " + ip + " is UP !")
            break
        
    condition_adhoc.notify()
    condition_adhoc.release()
    time.sleep(random.random())


def sendFile(dest, txt):
    myssh = connectToPi(ip=dest)
    routeFile(myssh, txt)
    myssh.close()


# if danger > 1
# else 0
# return randNum
def isDanger(sound):  # for part 2
    print("thishtilsht;alkj;fljf;ekfjlej")
    pred = getDetectionResult(sound)
    #print('\t',y_pred)
    
    #pred = random.randrange(0, 2)
    print("this is pred !!!!" + str(pred))
    return pred
    #return 0


def alert(detectedNode):
    idx = int(detectedNode)
    condition_alert.acquire()
    if ALERT_TABLE[idx] == 0:
        ALERT_TABLE[idx] = 1
        print(str(idx)+"th node detected")
    condition_alert.notify()
    condition_alert.release()


def checkWav(sound):  # for part 2
    print("chek wav")
    global isWork
    isWork = isWork + 1
    print(sound)
    if type(sound) == type(None):
        check = 0
    else:
        check = isDanger(sound)
    #print("check : ", check)
    if check == 1:
        # should route danger to neighbor node
        print("it is danger")
        lightUpTwoLED()
        if IS_MANAGER == 1:
            alert(int(MINE))
        else:
            adHocNetwork(ROUTE_PATH, MINE)
    else :
        lightUpOneLED()


def soundRecord():
    frames = []
    for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK, exception_on_overflow=False)
        frames.append(data)
    frame_ = b''.join(frames)
    audio = np.fromstring(frame_, np.int16)
    return audio[:]/32768


class ProducerThread(Thread):
    def run(self):
        nums = range(5)
        global queue
        global count
        global in_queue
        global out_queue
        while True:
            condition_queue.acquire()
            if count == MAX_NUM:
                print('Queue full, producer is waiting')
                condition_queue.wait()
                print("Space in queue, Consumer notified the producer")
            input = soundRecord()
            #fileNum = random.randrange(1, 11)
            #wavFilePath = "./gunhoo/"+str(fileNum)+".wav"
            #print("wavFilePath :"+wavFilePath)
            #fs, input = wavfile.read(wavFilePath)
            #input = 1
            queue[in_queue] = input
            in_queue = (in_queue + 1) % MAX_NUM
            count += 1

            condition_queue.notify()
            condition_queue.release()
            time.sleep(random.random())


class ConsumerThread(Thread):
    def run(self):
        global queue
        global count
        global in_queue
        global out_queue
        while True:
            condition_queue.acquire()
            if count == 0:
                print("Nothing in queue, consumer is waiting")
                condition_queue.wait()
                print("Producer added something to queue and notifed the consumer")
            output = queue[out_queue]
            out_queue = (out_queue + 1) % MAX_NUM
            condition_queue.notify()
            condition_queue.release()
            checkWav(output)
            #time.sleep(random.random())



def isManager(myPiAddress):
    global managers
    global managerList
    #managerList = managerList[0:len(managerList)-1]
    managers = managerList.split(" ")
    managers[1] = getProferNode(managers[1])
    for i in range(0, len(managers)):
        if (managers[i] == str(myPiAddress)):
            return 1
    return 0


def isYouCouple():
    
    # set couple_left , couple_right
    global couple_left
    global couple_right
    global left_idx
    global right_idx
    global mid
    
    mid = (node_list[0] + node_list[num_of_nodes - 1]) / 2
    couple_left = 0
    couple_right = 999999

    if num_of_nodes % 2 == 0:
        for i in range(0, num_of_nodes):
            if (node_list[i] < mid and couple_left < node_list[i]):
                couple_left = node_list[i]
                left_idx = i
                #print("isyoucoule left idx", i)
            elif (node_list[i] > mid and couple_right > node_list[i]):
                couple_right = node_list[i]
                right_idx = i
    else:
        mid_idx = int((num_of_nodes - 1) / 2)
        couple_left = node_list[mid_idx]
        couple_right = node_list[mid_idx + 1]
        left_idx = mid_idx
        right_idx = mid_idx + 1
    #print("isyoucoule end left idx", left_idx)
    #print("left", couple_left)
    #print("right", couple_right)
    #print("left idx", left_idx)
    #print("right idx", right_idx)
    #print("my idx", my_idx)


class IsChangeThread(Thread):
    def run(self):
        global ROUTE_PATH
        global num_of_nodes
        global start_of_nodeId
        # global ip_list
        global node_list
        global IS_MANAGER
        global next_node
        global pre_node
        global couple_left
        global couple_right
        global left_idx
        global right_idx
        global my_idx
        global mid
        global managers
        global managerList

        while True:
            while True:
                try:
                    f = open('info.txt', 'r')
                    break
                except FileNotFoundError:
                    print("info.txt File Not Found Error ! I try again!")
            
            #f = open('info.txt', 'r')
            line = f.readline()
            node_num_file = int(line)
            temptxt = line
            start_of_nodeId = int(f.readline())
            temptxt = temptxt + str(start_of_nodeId) + "\n"
            ip_list = [None] * (node_num_file)
            org_node_list = list(node_list)
            node_list = [None] * (node_num_file)

            flag = 0
            if (node_num_file != num_of_nodes):
                flag = 1
                num_of_nodes = node_num_file

            for i in range(0, node_num_file):
                ip_list[i] = f.readline()
                temptxt += ip_list[i]
                # print(ip_list[i])
                tempstr = "192.168.1." + str(MINE) + "\n"
                tempstr2 = ip_list[i]
                if (tempstr == tempstr2):
                    my_idx = i
                node_list[i] = int(ip_list[i][10:])

            # check manager
            ### !!! HERE SEOJEONG !!!
            managerList = f.readline()
            temptxt = temptxt + managerList + "\n"
            f.close()
            #print(temptxt)
            IS_MANAGER = isManager(node_list[my_idx])
            if flag == 1:
                for i in range(0, num_of_nodes) :
                    if org_node_list[i] != node_list[i] :
                        del_idx = i
                        break
                    if i == (num_of_nodes -1) :
                        del_idx = i+1
                if IS_MANAGER == 1:
                    del ALERT_TABLE[org_node_list[del_idx]]

            # Couple setting
            isYouCouple()
            isSSHworks = 0
            if IS_MANAGER == 0 :
                if int(MINE) <= couple_left :
                    ROUTE_PATH = ip_list[my_idx - 1]
                else :
                    ROUTE_PATH = ip_list[my_idx + 1]
                # sys.exit(1)
                #print("couple_right",couple_right)
                if (int(MINE) == couple_left):
                    ip=ip_list[right_idx]
                    cnt = 0
                    while True:
                        status,result = sp.getstatusoutput("ping -c1 -w2 " + ip)
    
                        if(status != 0 and cnt >2):
                            isSSHworks = 0
                            print("system " + ip + " is DOWN !")
                            cnt = 0
                            break
                        elif(status != 0):
                            cnt = cnt + 1
                        else:
                            isSSHworks=1
                            print("system " + ip + " is UP !")
                            break
               
                            
                elif (int(MINE) == couple_right):
                    ip=ip_list[left_idx]
                    cnt = 0
                    while True:
                        status,result = sp.getstatusoutput("ping -c1 -w2 " + ip)
    
                        if(status != 0 and cnt >2):
                            isSSHworks = 0
                            print("system " + ip + " is DOWN !")
                            cnt = 0
                            break
                        elif(status != 0):
                            cnt = cnt + 1
                        else:
                            isSSHworks=1
                            print("system " + ip + " is UP !")
                            break                 
                else:
                    if (node_list[my_idx] < mid) :
                        ip = ip_list[my_idx - 1]
                    elif (node_list[my_idx] >= mid) :
                        ip = ip_list[my_idx + 1]
                          
                    cnt = 0
                    while True:
                        status,result = sp.getstatusoutput("ping -c1 -w2 " + ip)
    
                        if(status != 0 and cnt >2):
                            isSSHworks = 0
                            print("system " + ip + " is DOWN !")
                            cnt = 0
                            break
                        elif(status != 0):
                            cnt = cnt + 1
                        else:
                            isSSHworks=1
                            print("system " + ip + " is UP !")
                            break
                    
            if (isSSHworks == 1):
                if (flag == 1):
                    if (IS_MANAGER == 0) :
                        if (int(org_node_list[del_idx]) < int(MINE)) :
                            sendFile(ip_list[my_idx + 1], temptxt)
                        else :
                            sendFile(ip_list[my_idx - 1], temptxt)


            # couple is dead
            ### !!! HERE SEOJEONG !!!
            elif (isSSHworks == 0):
                #cmd = 'python pyissshworksaudioPlayer.py'
                #os.system(cmd)
                
                
                if int(MINE) == couple_left:  # when right side is dead (here, node 4)
                    changeInfo(ip_list[right_idx])  # write new file
                    next_node = ip_list[right_idx + 1]
                    pre_node = ip_list[left_idx - 1]
                    sendFile(next_node, txt)
                    sendFile(pre_node, txt)
                    

                elif int(MINE) == couple_right:
                    changeInfo(ip_list[right_idx])  # write new file
                    next_node = ip_list[right_idx + 1]
                    pre_node = ip_list[left_idx - 1]
                    sendFile(next_node, txt)
                    sendFile(pre_node, txt)

                else:
                    if IS_MANAGER == 0 :
                        if (node_list[my_idx] < mid) :
                            if isManager(node_list[my_idx-1]) == 1:
                                if start_of_nodeId == node_list[my_idx-1] :
                                    start_of_nodeId = node_list[my_idx]
                                #managers = managerList.split(" ")
                                for i in range(0, len(managers)):
                                    if (managers[i] == str(node_list[my_idx-1])):
                                        managers[i] = str(node_list[my_idx])
                                    else :
                                        managers[i] = managers[i]
                                managerList = str(managers[0]) + " " + str(managers[1]) + "\n"
                                IS_MANAGER = 1
                                lightUpOneLED()
                                LEDThread().start()
                                CheckFileThread().start()
                                changeInfo(ip_list[my_idx - 1])
                                next_node = ip_list[my_idx + 1]
                                sendFile(next_node, txt)  # send file to next node
                            else:
                                changeInfo(ip_list[my_idx - 1])  # write new file
                                next_node = ip_list[my_idx + 1]
                                pre_node = ip_list[my_idx - 2]
                                sendFile(next_node, txt)  # send file to next node
                                sendFile(pre_node, txt)  # send file to previous node
                        
                        elif (node_list[my_idx] >= mid) :
                            if isManager(node_list[my_idx+1]) == 1:
                                if start_of_nodeId == node_list[my_idx+1] :
                                    start_of_nodeId = node_list[my_idx]
                                #managers = managerList.split(" ")
                                for i in range(0, len(managers)):
                                    if (managers[i] == str(node_list[my_idx+1])):
                                        managers[i] = str(node_list[my_idx])
                                managerList = str(managers[0]) + " " + str(managers[1]) + "\n"
                                IS_MANAGER = 1
                                lightUpOneLED()
                                LEDThread().start()
                                CheckFileThread().start()
                                changeInfo(ip_list[my_idx + 1])  # write new file
                                pre_node = ip_list[my_idx - 1]
                                sendFile(pre_node, txt)  # send file to previous node
                            else:
                                changeInfo(ip_list[my_idx + 1])  # write new file
                                next_node = ip_list[my_idx + 2]
                                pre_node = ip_list[my_idx - 1]
                                sendFile(next_node, txt)  # send file to next node
                                sendFile(pre_node, txt)  # send file to previous node
                            
                        
                        
                    #elif IS_MANAGER == 1 :
                       # if int(MINE) > couple_right :
                            #del ALERT_TABLE[node_list[my_idx-1]]
                        #else :
                            #del ALERT_TABLE[node_list[my_idx+1]]
                
                while True:
                    try:
                        f = open('info.txt', 'r')
                        break
                    except FileNotFoundError:
                        print("info.txt File Not Found Error ! I try again!")
            
                #f = open('info.txt', 'r')
                line = f.readline()
                node_num_file = int(line)
                ip_list = [None] * (node_num_file)
                node_list = [None] * (node_num_file)

                num_of_nodes = node_num_file
                start_of_nodeId = f.readline()

                for i in range(0, node_num_file):
                    ip_list[i] = f.readline()
                    #ip_list[i] = ip_list[i][0:len(ip_list[i])-1]
                    temptxt += ip_list[i]
                    tempstr = "192.168.1." + str(MINE) + "\n"
                    tempstr2 = ip_list[i]
                    if (tempstr == tempstr2):
                        my_idx = i
                    
                    node_list[i] = int(ip_list[i][10:])
                f.close()

def checkFile():
    while True:
        print("in checkFile func")
        for i in range(0, 5):
            while True:
                try:
                    f = open(INPUT_FILE[i], 'r')
                    print("checking " + str(i) +"th file")
                    break
                except FileNotFoundError:
                    print(INPUT_FILE[i]+ "File Not Found Error ! I try again!")

            #f = open(INPUT_FILE[i], 'r')
            line = f.readline()
            idx = line.find('from')
            
            if idx == -1:
                f.close()
            else :
                # print("checked file : " + line)
                nodes = line.split("from")
                nodes[1] = getProferNode(nodes[1])
                alert(int(nodes[1]))

class CheckFileThread(Thread) :
    def run(self) :
        checkFile()

def lightUpOneLED():
    for i in range(0, 2):
        GPIO.output(23, False)
        time.sleep(1)
        GPIO.output(23, True)
        time.sleep(1)


def lightUpTwoLED():
    for i in range(0, 2):
        print(str(i) + "turn on")
        GPIO.output(24, True)
        GPIO.output(23, True)
        time.sleep(1)
        print(str(i) + "turn off")
        GPIO.output(24, False)
        GPIO.output(23, False)
        time.sleep(1)

class CountThreadThread(Thread) :
    def run(self) :
        numOfThread = threading.active_count()
        print("the roop has !! " + str(numOfThread) + "threads !!")
        time.sleep(1)

class LEDThread(Thread):
    def run(self):
        #print("running thread")
        global ALERT_TABLE
        while True:
            howManyDetected = 0
            isMiddle = 0
            condition_alert.acquire()
            for i in range(1, num_of_nodes + 1):
                try :
                    if ALERT_TABLE[node_list[i]] == 1:
                        print(str(node_list[i]) + "node detected")
                        howManyDetected = howManyDetected + 1
                        ALERT_TABLE[node_list[i]] = 0
                        if node_list[i] == couple_left or node_list[i] == couple_right:
                            isMiddle = 1
                    else :
                        #print("no detection")
                        block = 0
                except IndexError :
                    block = 1
                    #print("wrong access to ALERT_TABLE")
                except KeyError :
                    block = 2
                    #print("wrong access to ALERT_TABLE , keyError")
            condition_alert.notify()
            condition_alert.release()
            #print("3 " + str(howManyDetected))
            if howManyDetected == 1:
                if isMiddle == 1:
                    lightUpTwoLED()
                else:
                    lightUpOneLED()
                print("one")
            elif howManyDetected != 0:
                print("several")
                lightUpTwoLED()

def getProferNode(node) :
    for i in range(0, len(node)) :
        if node[i].isdigit() == False :
            return node[0:i]
    return node

def checkDetection():  # for part 3
    global TARGET_MINE
    while True:
        while True:
            try:
                f = open(INPUT_FILE[TARGET_MINE], 'r')
                break
            except FileNotFoundError:
                print(INPUT_FILE[TARGET_MINE]+ "File Not Found Error ! I try again!")
        
        #f = open(INPUT_FILE[TARGET_MINE], 'r')
        line = f.readline()
        idx = line.find('from')
        condition_detect.acquire()
        if idx == -1:
            f.close()
        else:
            line = line[0:len(line)]
            print("This is line : ", line)
            nodes = line.split("from")
            f.close()
            # destPi = ROUTING_TABLE[nodes[0]]
            if IS_MANAGER == 1:
                nodes[1] = getProferNode(nodes[1])
                alert(nodes[1])
            else:
                adHocNetwork(ROUTE_PATH, nodes[1])
            #print("in check detect fuck nodes[0]", nodes[0])
            #print("in check detect fuck nodes[1]", nodes[1])
            # print("in check detect fuck destPi", destPi)
            
            while True:
                try:
                    f = open(INPUT_FILE[TARGET_MINE], 'w+')
                    break
                except FileNotFoundError:
                    print(INPUT_FILE[TARGET_MINE] + "File Not Found Error ! I try again!")
                
            #f = open(INPUT_FILE[TARGET_MINE], 'w+')
            f.write(NO_DETECTION)
            f.close()
            TARGET_MINE = (TARGET_MINE + 1) % NUM_OF_FILE
        condition_detect.notify()
        condition_detect.release()


def initializeVars():
    global node_num_file
    global num_of_nodes
    global start_of_nodeId
    # global ip_list
    global node_list
    global IS_MANAGER
    global ROUTE_PATH
    global my_idx
    global ALERT_TABLE
    global managerList
    
    while True:
        try:
            f = open(INFO_FILE, 'r')
            break
        except FileNotFoundError:
            print(INFO_FILE+ "File Not Found Error ! I try again!")
        
    
    #f = open(INFO_FILE, 'r')
    line = f.readline()
    node_num_file = int(line)
    num_of_nodes = int(line)
    line = f.readline()
    start_of_nodeId = int(line)

    temp_ip = [None] * (node_num_file)
    node_list = [None] * (node_num_file)
    for i in range(0, node_num_file):
        temp_ip[i] = f.readline()
        #print("temp_ip[i]", temp_ip[i])
        node_list[i] = int(temp_ip[i][10:])
        if node_list[i] == int(MINE) :
            my_idx = i
    isYouCouple()
    managerList = f.readline()
    #print(temp_ip[my_idx])
    IS_MANAGER = isManager(node_list[my_idx])
    #print("IS MA", IS_MANAGER)
    #print("couple_left",couple_left)
    if IS_MANAGER == 0 :
        if int(MINE) <= couple_left :
            ROUTE_PATH = temp_ip[my_idx-1]
            print("temp_ip[my_idx-1]",temp_ip[my_idx-1])
            
        else :
            ROUTE_PATH = temp_ip[my_idx+1]
            print("temp_ip[my_idx+1]",temp_ip[my_idx+1])
    else :
        for i in range(0, node_num_file) :
            ALERT_TABLE[node_list[i]] = 0
    print("ROUTH_PATH : ",ROUTE_PATH)

    # seojeong should complete this function and call this func. when this file starts

#cmd = 'python pyaudioPlayer.py'
#os.system(cmd)

initializeVars()
CountThreadThread().start()
ProducerThread().start()

consumerList = [ConsumerThread() for i in range(0, 6)]
for i in range(0, 6):
    consumerList[i].start()

IsChangeThread().start()

if IS_MANAGER == 1:
    #lightUpOneLED()
    LEDThread().start()
    CheckFileThread().start()

checkDetection()  # for part 3

# start()
# sendFile(next_node,txt)
# sendFile(pre_node,txt)


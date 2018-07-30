from paramiko import SSHClient, AutoAddPolicy
import random
import pyaudio
import wave
from threading import Thread, Condition
import time
import sys
import RPi.GPIO as GPIO

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
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
RECORD_SECONDS = 0.2

p = pyaudio.PyAudio()

stream = p.open(format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK)

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
MINE = "1"
ROUTING_TABLE = {'3': 2, '2': 3}
ROUTE_PATH = '192.168.1.2'
#IP_TABLE = {3: '192.168.1.3', 2: '192.168.1.2'}

num_of_nodes = 100
start_of_nodeId = 0 # add ittttt
txt = ""
next_node = 0
pre_node = 0
#ip_list = [None] * (num_of_nodes)
#node_list = [None] * (num_of_nodes)
ip_list = []
node_list = []
couple_left = 0
couple_right = 0
left_idx = 0
right_idx = 0
my_idx = 0

ALERT_TABLE = {1: 0, 2: 0, 3: 0}  # NODE : IS_DETECTED
#numOfNode = 3
condition_alert = Condition()

def connectToPi(ip, username='pi', pw='1357'):
    # print('connecting to {}@{}...'.format(username,ip))
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
    print("JUST WROTE" + replaceStr + "IT'S TARGET WAS " + str(TARGET_OTHER))
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
def adHocNetwork(dest, src):
    condition_adhoc.acquire()
    myssh = connectToPi(ip=dest)
    routeDetection(myssh, src)
    condition_adhoc.notify()
    condition_adhoc.release()
    time.sleep(random.random())


def sendFile(dest, txt):
    myssh = connectToPi(ip=dest)
    routeFile(myssh, txt)


# write new filech
def changeInfo(ip):
    global num_of_nodes
    global txt

    num_of_nodes = num_of_nodes - 1

    f = open('info.txt', 'r')
    line = f.readline()
    lines = f.readlines()
    f.close()

    f = open('info.txt', 'w')
    f.write(str(num_of_nodes) + '\n')
    txt = str(num_of_nodes) + "\n"
    for i in lines:
        if i != ip:
            f.write(i)
            txt += i


# if danger > 1
# else 0
# return randNum
def isDanger():  # for part 2
    randNum = random.randrange(0, 2)
    return 0

def alert(detectedNode):
    condition_alert.acquire()
    if ALERT_TABLE[detectedNode] == 0:
        ALERT_TABLE[detectedNode] = 1
    condition_alert.notify()
    condition_alert.release()

def checkWav(sound):  # for part 2
    global isWork
    isWork = isWork + 1
    check = isDanger()
    if check == 1:
        # should route danger to neighbor node
        print("it is danger")
        if IS_MANAGER == 1 :
            alert(int(MINE))
        else :
            adHocNetwork(ROUTE_PATH, MINE)


def soundRecord():
    frames = []
    for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK, exception_on_overflow=False)
        frames.append(data)
    return b''.join(frames)


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
            # input = soundRecord()
            input = 1
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
            time.sleep(random.random())


def isManager(managerList):
    managers = managerList.split(" ")
    for i in range(0, len(managers)):
        if (int(managers[i]) == MINE):
            return '1'
    return '0'


def isYouCouple() :
    mid = (node_list[0] + node_list[num_of_nodes - 1]) / 2
    # set couple_left , couple_right
    couple_left = 0
    couple_right = 999999
    
    if num_of_nodes %2 == 0 :
        for i in range(0, num_of_nodes):
            if (node_list[i] < mid and couple_left < node_list[i]):
                couple_left = node_list[i]
                left_idx = i
            elif (node_list[i] > mid and couple_right > node_list[i]):
                couple_right = node_list[i]
                right_idx = i
    else :
        mid_idx = int((num_of_nodes-1)/2)
        couple_left = node_list[mid_idx]
        couple_right = node_list[mid_idx+1]
        left_idx = mid_idx
        right_idx = mid_idx +1

    print("left", couple_left)
    print("right", couple_right)
    print("left idx", left_idx)
    print("right idx", right_idx)
    print("my idx", my_idx)
    

class IsChangeThread(Thread):
    def run(self):
        global num_of_nodes
        global start_of_nodeId
        global ip_list
        global node_list
        global IS_MANAGER
        global next_node
        global pre_node
        global couple_left
        global couple_right
        global left_idx
        global right_idx
        global my_idx

        while True:
            f = open('info.txt', 'r')
            line = f.readline()
            if int(line) == num_of_nodes:
                f.close()
            else:
                num_of_nodes = int(line)
                start_of_nodeId = int(f.readline())
                for i in range(0, num_of_nodes):
                    ip_list[i] = f.readline()
                    tempstr="192.168.1."+str(MINE)+"\n"
                    tempstr2=ip_list[i]
                    if(tempstr == tempstr2) :
                        my_idx = i
                    node_list[i] = int(ip_list[i][10:])
                    ip_list[i] = f.readline()
                    
                # check manager
                managerList = f.readline()
                f.close()
                IS_MANAGER = isManager(managerList)
                
                #Couple setting
                isYouCouple()

                isSSHworks = -1
                # sys.exit(1)

                if (MINE == couple_left):
                    try:
                        myssh = connectToPi(ip=ip_list[right_idx])
                        isSSHworks = 1
                        print("ssh success : ", ip_list[right_idx])
                    except paramiko.ssh_exception.NoValidConnectionsError:
                        isSSHworks = 0
                        print("ssh fail")
                elif (MINE == couple_right):
                    try:
                        myssh = connectToPi(ip=ip_list[left_idx])
                        isSSHworks = 1
                        print("ssh success : ", ip_list[left_idx])
                    except paramiko.ssh_exception.NoValidConnectionsError:
                        isSSHworks = 0
                        print("ssh fail")
                        
                else :
                    try:
                        myssh = connectToPi(ip=ip_list[my_idx+1])
                        isSSHworks=1
                        print("ssh success : ",ip_list[my_idx+1])
                    except paramiko.ssh_exception.NoValidConnectionsError:
                        isSSHworks=0
                        print("ssh fail")
                        
                        
                # couple is dead
                if (isSSHworks == 0):  
                    if MINE == couple_left:  # when right side is dead (here, node 4)
                        changeInfo(ip_list[right_idx])  # write new file
                        next_node = ip_list[right_idx + 1]
                        pre_node = ip_list[left_idx - 1]
                        sendFile(next_node, txt)
                        sendFile(pre_node, txt)

                    elif MINE == couple_right:
                        changeInfo(ip_list[right_idx])  # write new file
                        next_node = ip_list[right_idx + 1]
                        pre_node = ip_list[left_idx - 1]
                        sendFile(next_node, txt)
                        sendFile(pre_node, txt)
                        
                    else :
                        changeInfo(ip_list[my_idx+1]) #write new file
                        next_node = ip_list[my_idx+2]
                        pre_node = ip_list[my_idx-1]
                        sendFile(next_node, txt) #send file to next node
                        sendFile(pre_node, txt) #send file to previous node

def checkFile():
    while True:
        for i in range(0, 5):
            f = open(INPUT_FILE[i], 'r')
            line = f.readline()
            # print("checked file : " + line)
            if line[1:5] == 'from':
                line = line[5:6]
                f.close()
                alert(int(line))


def lightUpOneLED():
    for i in range(0, 2):
        GPIO.output(23, False)
        time.sleep(1)
        GPIO.output(23, True)
        time.sleep(1)


def lightUpTwoLED():
    for i in range(0, 2):
        GPIO.output(24, False)
        GPIO.output(23, False)
        time.sleep(1)
        GPIO.output(24, True)
        GPIO.output(23, True)
        time.sleep(1)


class LEDThread(Thread):
    def run(self):
        print("running thread")
        global ALERT_TABLE
        while True:
            howManyDetected = 0
            isMiddle = 0
            condition_alert.acquire()
            for i in range(1, num_of_nodes + 1):
                if ALERT_TABLE[i] == 1:
                    print(str(i) + "node detected")
                    howManyDetected = howManyDetected + 1
                    ALERT_TABLE[i] = 0
                    if i == num_of_nodes:
                        isMiddle = 1
            condition_alert.notify()
            condition_alert.release()
            print("3 " + str(howManyDetected))
            if howManyDetected == 1:
                if isMiddle == 1:
                    lightUpTwoLED()
                else:
                    lightUpOneLED()
                print("one")
            elif howManyDetected != 0:
                print("several")
                lightUpTwoLED()

def checkDetection():  # for part 3
    global TARGET_MINE
    while True:
        f = open(INPUT_FILE[TARGET_MINE], 'r')
        line = f.readline()
        idx = line.find('from')
        condition_detect.acquire()
        if idx == -1:
            f.close()
        else:
            for i in range(idx+4,len(line)):
                if int(line[i])>-1 and int(line[i])<10 :
                    last_idx = i
                    print("last_idx : ", last_idx)
                    
            line = line[0:last_idx+1] 
            print("This is line : ", line)
            nodes = line.split("from")
            f.close()
            # destPi = ROUTING_TABLE[nodes[0]]
            if IS_MANAGER == 1 :
                alert(nodes[1])
            else :
                adHocNetwork(ROUTE_PATH, nodes[1])
            print("in check detect fuck nodes[0]", nodes[0])
            print("in check detect fuck nodes[1]", nodes[1])
            # print("in check detect fuck destPi", destPi)
            f = open(INPUT_FILE[TARGET_MINE], 'w+')
            f.write(NO_DETECTION)
            f.close()
            TARGET_MINE = (TARGET_MINE + 1) % NUM_OF_FILE
        condition_detect.notify()
        condition_detect.release()

def initializeVars() :
    global num_of_nodes
    global start_of_nodeId
    global ip_list
    global node_list
    global IS_MANAGER
    global next_node
    global pre_node

    f = open(INFO_FILE, 'r')
    line = f.readline()
    num_of_nodes = int(line)
    start_of_nodeId = int(line)
    for i in range(0, num_of_nodes):
        ip_list[i] = f.readline()
        node_list[i] = int(ip_list[i][10:])
    managerList = f.readline()
    IS_MANAGER = isManager(managerList)
    # seojeong should complete this function and call this func. when this file starts


IS_MANAGER = sys.argv[1]

ProducerThread().start()

consumerList = [ConsumerThread() for i in range(0, 10)]
for i in range(0, 10):
    consumerList[i].start()

IsChangeThread().start()

if IS_MANAGER == 1 :
    LEDThread().start()

checkDetection()  # for part 3

# start()
# sendFile(next_node,txt)
# sendFile(pre_node,txt)



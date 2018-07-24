from paramiko import SSHClient, AutoAddPolicy
import random
import pyaudio
import wave
from threading import Thread, Condition
import time

NO_DETECTION = "node"
INPUT_FILE = ["/home/pi/detect1.txt", "/home/pi/detect2.txt", "/home/pi/detect3.txt", "/home/pi/detect4.txt", "/home/pi/detect5.txt"]
NUM_OF_FILE = 5
TARGET_MINE = 0
TARGET_OTHER = 0

# var for part 1 starts
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
RECORD_SECONDS = 0.2

p = pyaudio.PyAudio()

stream = p.open(format = FORMAT,
                channels = CHANNELS,
                rate = RATE,
                input = True,
                frames_per_buffer = CHUNK)

MAX_NUM=10
queue = [None]*MAX_NUM
condition_queue = Condition()
condition_adhoc = Condition()
condition_detect = Condition()
in_queue = 0
out_queue = 0
count = 0
isWork=0
#var for part 1 ends

#first node side
MINE = "1"
ROUTING_TABLE = {'3':2, '2':3}
ROUTE_PATH = '192.168.1.2'
IP_TABLE = {3:'192.168.1.3', 2:'192.168.1.2'}

def connectToPi(ip, username='pi', pw='1357') :
    #print('connecting to {}@{}...'.format(username,ip))
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())
    ssh.connect(ip,username=username,password=pw)
    return ssh

def sendCommand(ssh, command, pw='1357') :
    stdin, stdout, stderr = ssh.exec_command(command)
    if "sudo" in command :
        stdin.write(pw+'\n')
    stdin.flush()
    #print('\nstdout : ',stdout.read())
    #print('\nstderr : ',stderr.read())

# routing detection to destNode
# write [MINE] + from + [srcNode] in detect.txt
def routeDetection(myssh, srcNode) :
    global TARGET_OTHER
    replaceStr = MINE + "from" +srcNode
    input_file = INPUT_FILE[TARGET_OTHER].split("/home/pi/")
    cmd = "vi -c \"%s/node/"+replaceStr+"/g\" -c \"wq\" " + input_file[1]+""
    #print("JUST WROTE" + replaceStr + "IT'S TARGET WAS " + str(TARGET_OTHER))
    TARGET_OTHER  =  (TARGET_OTHER + 1)%NUM_OF_FILE
    sendCommand(myssh, command=cmd)
    
# check detection recursively
# if line is "node" -> no detection
# else detection -> route detection to neighbor node
# nodes[0] : neighbor node
# nodes[1] : source node
def adHocNetwork(dest, src) :
    condition_adhoc.acquire()
    myssh = connectToPi(ip=dest)
    routeDetection(myssh, src)
    condition_adhoc.notify()
    condition_adhoc.release()
    time.sleep(random.random())

def checkDetection() : # for part 3
    global TARGET_MINE
    while True:
        f = open(INPUT_FILE[TARGET_MINE],'r')
        line = f.readline()
        condition_detect.acquire()
        if len(line) != 6 : 
            f.close()
        else :
            print("This is line : ",line)
            nodes = line.split("from")
            f.close()
            #destPi = ROUTING_TABLE[nodes[0]]
            adHocNetwork(ROUTE_PATH, nodes[1])
            print("in check detect fuck nodes[0]" , nodes[0])
            print("in check detect fuck nodes[1]", nodes[1])
            #print("in check detect fuck destPi", destPi)
            f = open(INPUT_FILE[TARGET_MINE],'w+') 
            f.write(NO_DETECTION)
            f.close()
            TARGET_MINE = (TARGET_MINE +1)%NUM_OF_FILE 
        condition_detect.notify()
        condition_detect.release()

# if danger > 1
# else 0
#return randNum
def isDanger() : # for part 2
    randNum = random.randrange(0,2)
    return 1

def checkWav(sound) : # for part 2
    global isWork
    isWork = isWork+1
    check = isDanger()
    if check == 1 :
        # should route danger to neighbor node
        adHocNetwork(ROUTE_PATH, MINE)

def soundRecord() :
    frames = []
    for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK)
        frames.append(data)
    return b''.join(frames)

class ProducerThread(Thread):
    def run(self):
        nums=range(5)
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
            #input = soundRecord()
            input = 1
            queue[in_queue]= input
            in_queue = (in_queue+1)%MAX_NUM
            count +=1
            
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
                print ("Nothing in queue, consumer is waiting")
                condition_queue.wait()
                print ("Producer added something to queue and notifed the consumer")
            output = queue[out_queue]
            out_queue = (out_queue+1) % MAX_NUM
            condition_queue.notify()
            condition_queue.release()
            checkWav(output)
            time.sleep(random.random())
    

ProducerThread().start()

consumerList = [ConsumerThread() for i in range(0,10)]
for i in range(0,10):
    consumerList[i].start()

checkDetection() # for part 3


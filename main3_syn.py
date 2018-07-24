from paramiko import SSHClient, AutoAddPolicy
import random
import pyaudio
import wave
from threading import Thread, Condition
import time

NO_DETECTION = "node"
TARGET_MINE= 0
TARGET_OTHER= 0
NUM_OF_FILE = 5

INPUT_FILE = ["/home/pi/detect1.txt","/home/pi/detect2.txt","/home/pi/detect3.txt","/home/pi/detect4.txt","/home/pi/detect5.txt"]

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

#third node side
MINE = "3"
ROUTING_TABLE = {'1':2, '2':1}
ROUTE_PATH = '192.168.1.1'
IP_TABLE = {1:'192.168.1.1', 2:'192.168.1.2'}


def connectToPi(ip, username='pi', pw='1357') :
    print('connecting to {}@{}...'.format(username,ip))
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())
    ssh.connect(ip,username=username,password=pw)
    print('connection status = ',ssh.get_transport().is_active())
    return ssh

def sendCommand(ssh, command, pw='1357') :
    #print('sending a command . . . ', command)
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
    global TARGET_MINE
    replaceStr = MINE + "from" +srcNode
    input_file = INPUT_FILE[TARGET_OTHER].split("/home/pi/")
    cmd = "vi -c \"%s/node/"+replaceStr+"/g\" -c \"wq\" " + input_file[1] +""
    print(cmd)
    #print("JUST WROTE" + replaceStr + "It's target was " + str(TARGET_OTHER))
    TARGET_OTHER = (TARGET_OTHER +1) % NUM_OF_FILE
    sendCommand(myssh, command=cmd)
    
# check detection recursively
# if line is "node" -> no detection
# else detection -> route detection to neighbor node
# nodes[0] : neighbor node
# nodes[1] : source node
def adHocNetwork(dest, src) :
    condition_adhoc.acquire()
    print("in adhoc fuck dest" , dest)
    print("in adhoc fuck src", src)
    myssh = connectToPi(ip=dest)
    routeDetection(myssh, src)
    condition_adhoc.notify()
    condition_adhoc.release()
    time.sleep(random.random())

def checkDetection() : # for part 3
    global TARGET_OTHER
    global TARGET_MINE
    while True:
        f = open(INPUT_FILE[TARGET_MINE],'r')
        line = f.readline()
        condition_detect.acquire()
        if line[1:5]!= 'from' :
            f.close()
        else :
            line = line[0:6]
            print("This is line : ",line)
            nodes = line.split("from")
            f.close()
            destPi = ROUTING_TABLE[nodes[0]]
            #adHocNetwork(IP_TABLE[destPi], nodes[1])
            adHocNetwork(ROUTE_PATH,nodes[1])
            print("in check detect fuck nodes[0]" , nodes[0])
            print("in check detect fuck nodes[1]", nodes[1])
            print("in check detect fuck destPi", destPi)
            f = open(INPUT_FILE[TARGET_MINE],'w+')
            f.write(NO_DETECTION)
            f.close()
            TARGET_MINE = (TARGET_MINE +1) % NUM_OF_FILE
        condition_detect.notify()
        condition_detect.release()
    #checkDetection()

def isDanger() : # for part 2
    randNum = random.randrange(0,2)
    # if danger > 1
    # else 0
    #return randNum
    return 1

def checkWav(sound) : # for part 2
    # check sound
    global isWork
    isWork = isWork+1
    #print(isWork)
    check = isDanger()
    #print(check)
    if check == 1 :
        # should route danger to neighbor node
        adHocNetwork(ROUTE_PATH, MINE)

def soundRecord() :
    #print("start to record the audio.")
    frames = []
    #print(len(frames))
    for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK,exception_on_overflow = False)
        frames.append(data)
    
    # print("Recording finished.")
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
            input = soundRecord()
            #input=1
            queue[in_queue]= input
            in_queue = (in_queue+1)%MAX_NUM
            count +=1
            #print("Produced",input)
            
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
            #print ("Consumed",output)
            condition_queue.notify()
            condition_queue.release()
            checkWav(output)
            time.sleep(random.random())
    
ProducerThread().start()

consumerList = [ConsumerThread() for i in range(0,10)]
for i in range(0,10):
    consumerList[i].start()

checkDetection() # for part 3


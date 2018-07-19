from paramiko import SSHClient, AutoAddPolicy
import random
import pyaudio
import wave
from threading import Thread, Condition
import time

NO_DETECTION = "node"
INPUT_FILE = "/home/pi/detect.txt"

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
condition = Condition()
in_queue = 0
out_queue = 0
count = 0
#var for part 1 ends

#first node side
MINE = "1"
ROUTING_TABLE = {'3':2, '2':3}
ROUTE_PATH = '192.168.1.2'
IP_TABLE = {3:'192.168.1.3', 2:'192.168.1.2'}

isWork = 0

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
def adHocNetwork(dest, src) :
    condition.acquire()
    myssh = connectToPi(ip=dest)
    routeDetection(myssh, src)
    condition.notify()
    condition.release()
    time.sleep(random.random())

def checkDetection() : # for part 3
    f = open(INPUT_FILE,'r')
    line = f.readline()
    if line == NO_DETECTION :
        f.close()
    else :
        nodes = line.split("from")
        f.close()
        destPi = ROUTING_TABLE[nodes[0]]
        adHocNetwork(IP_TABLE[destPi], nodes[1])
        f = open(INPUT_FILE,'w+')
        f.write(NO_DETECTION)
        f.close()
    checkDetection()

def isDanger() : # for part 2
    randNum = random.randrange(0,2)
    # if danger > 1
    # else 0
    return randNum

def checkWav(sound) : # for part 2
    # check sound
    isWork = isWork+1
    print(isWork)
    check = isDanger()
    print(check)
    if check == 1 :
        # should route danger to neighbor node
        adHocNetwork(ROUTE_PATH, MINE)

class ProducerThread(Thread):
    def run(self):
        nums=range(5)
        global queue
        global count
        global in_queue
        global out_queue
        while True:
            condition.acquire()
            if count == MAX_NUM:
                print('Queue full, producer is waiting')
                condition.wait()
                print("Space in queue, Consumer notified the producer")
            input = soundRecord()
            queue[in_queue]= input
            in_queue = (in_queue+1)%MAX_NUM
            count +=1
            print("Produced",input)
            
            condition.notify()
            condition.release()
            time.sleep(random.random())
            
    def soundRecord() :
        print("start to record the audio.")
        frames = []
        
        for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
            data = stream.read(CHUNK)
            frames.append(data)
    
        print("Recording finished.")
        return b''.join(frames)
            
class ConsumerThread(Thread):
    def run(self):
        global queue
        global count
        global in_queue
        global out_queue
        while True:
            condition.acquire()
            if count == 0:
                print ("Nothing in queue, consumer is waiting")
                condition.wait()
                print ("Producer added something to queue and notifed the consumer")
            output = queue[out_queue]
            out_queue = (out_queue+1) % MAX_NUM
            print ("Consumed",output)
            condition.notify()
            condition.release()
            checkWav(output)
            time.sleep(random.random())
    

ProducerThread().start()

consumerList = [ConsumerThread() for i in range(0,10)]
for i in range(0,10):
    consumerList[i].start()

checkDetection() # for part 3

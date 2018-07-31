import RPi.GPIO as GPIO
from threading import Thread, Condition
import time

GPIO.setmode(GPIO.BCM)
GPIO.setup(23,GPIO.OUT)
GPIO.setup(24,GPIO.OUT)

INPUT_FILE = ["/home/pi/detect1.txt","/home/pi/detect2.txt","/home/pi/detect3.txt","/home/pi/detect4.txt","/home/pi/detect5.txt"]

ALERT_TABLE = {1:0, 2:0, 3:0} # NODE : IS_DETECTED
numOfNode = 3
condition_alert = Condition()


def alert(detectedNode) :
    condition_alert.acquire()
    if ALERT_TABLE[detectedNode] == 0 :
       ALERT_TABLE[detectedNode] = 1
    condition_alert.notify()
    condition_alert.release()

def checkFile() :
    while True :
        for i in range(0, 5) :
            f = open(INPUT_FILE[i],'r')
            line = f.readline()
            #print("checked file : " + line)
            if line[1:5] == 'from' :
                line = line[5:6]
                f.close()
                alert(int(line))

def lightUpOneLED() :
    for i in range(0, 2) :
        GPIO.output(23,False)
        time.sleep(1)
        GPIO.output(23,True)
        time.sleep(1)
            
def lightUpTwoLED() :
    for i in range(0, 2) :
        GPIO.output(24,False)
        GPIO.output(23,False)
        time.sleep(1)
        GPIO.output(24,True)
        GPIO.output(23,True)
        time.sleep(1)

class LEDThread(Thread) :
    def run(self) :
        print("running thread")
        global ALERT_TABLE
        while True :
            howManyDetected = 0
            isMiddle = 0
            condition_alert.acquire()
            for i in range(1, numOfNode+1) :
                if ALERT_TABLE[i] == 1 :
                    print(str(i) + "node detected")
                    howManyDetected = howManyDetected + 1
                    ALERT_TABLE[i] = 0
                    if i == numOfNode :
                        isMiddle = 1
            condition_alert.notify()
            condition_alert.release()
            print("3 " +str(howManyDetected))
            if howManyDetected == 1 :
                if isMiddle == 1 :
                    lightUpTwoLED()
                else :
                    lightUpOneLED()
                print("one")
            elif howManyDetected != 0 :
                print("several")
                lightUpTwoLED()

LEDThread().start()
checkFile()
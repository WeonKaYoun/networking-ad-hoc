from threading import Thread, Condition
import time
import random

MAX_NUM=10
queue = [None]*MAX_NUM
condition = Condition()
in_queue = 0
out_queue = 0
count = 0

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
            input = random.choice(nums)
            queue[in_queue]= input
            in_queue = (in_queue+1)%MAX_NUM
            count +=1
            print("Produced",input)
            
            condition.notify()
            condition.release()
            time.sleep(random.random())
            
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
            time.sleep(random.random())

ProducerThread().start()
#ConsumerThread().start()

consumerList = [ConsumerThread() for i in range(0,5)]
for i in range(0,5):
    consumerList[i].start()
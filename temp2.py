num_of_nodes = 6
isAlive = 0
deadIP = "192.168.1.3"
nextIP = "192.168.1.4"

def checkInfo() :
    global num_of_nodes
    global isAlive

    if isAlive == 0 :
        f=open('info.txt','r')
        line = f.readline()
        #print(line)
        if int(line) == num_of_nodes :
            num_of_nodes = num_of_nodes-1
            #f.write(num_of_nodes)
            #print(num_of_nodes)
            lines=f.readlines()
            f.close()
            
            f=open('info2.txt','w')
            f.write(str(num_of_nodes)+'\n')
            for i in lines :
                if i != deadIP
                    print(i)
                    f.write(i)

checkInfo()
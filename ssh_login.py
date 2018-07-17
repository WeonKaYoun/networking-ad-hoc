#import paramiko

#ssh = paramiko.SSHClient()
#ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
#ssh.connect('192.168.1.2', username='pi', password='1357')
#cmd_to_execute='ls -al \n'
#stdin, stdout, stderr = ssh.exec_command(cmd_to_execute)

from paramiko import SSHClient, AutoAddPolicy


def Connect(ip,username='pi',pw='1357'):
    print('connecting to {}@{}...'.format(username,ip))
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())
    ssh.connect(ip,username=username,password=pw)
    print('connection status = ',ssh.get_transport().is_active())
    return ssh

def SendCommand(ssh,command, pw='1357'):
    print('sending a command...',command)
    stdin, stdout, stderr = ssh.exec_command(command)
    if "sudo" in command:
        stdin.write(pw+'\n')
    stdin.flush()
    print('\nstout:',stdout.read())
    print('\nstderr:',stderr.read())

myssh = Connect(ip='192.168.1.2')
#SendCommand(myssh, command='touch detect.txt')

data='node3 detection'
#SendCommand(myssh, command='cp node3.txt detect.txt')

#SendCommand(myssh, command='touch detect2.txt')
SendCommand(myssh, command='vim -c "%s/node/node3 detection/g" -c "wq" detect.txt')

#fb = open('detect.txt','w')
#fb.write(data + '\n')
#fb.close()


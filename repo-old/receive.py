'''import socket

HOST = '192.168.1.64'  # The server's hostname or IP address
PORT = 65432        # The port used by the server

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    s.sendall(b'Hello, world')
    data = s.recv(1024)

print('Received', repr(data))'''

# Import socket module 
import socket
import numpy

pi_ip = '172.20.10.3'
  
# Create a socket object 
s = socket.socket()          
  
# Define the port on which you want to connect 
port = 12357               
  
# connect to the pi
s.connect((pi_ip, port)) 

data = []
aaa = 9
# receive data from the server 
while True:
    temp_list = eval('(s.recv(1024).decode("utf-8"))')
    data.append(float(temp_list[1]))
    print(temp_list)
    temp_list = []
    if len(data)>aaa:
        c_avg = numpy.mean(data)
        f_avg = (c_avg*(9/5))+32
        print('''
data = %s
c_avg = %s
f_avg = %s

average of %s

resetting data array'''%(data,c_avg,f_avg,aaa+1))
        data = []
    # close the connection 
    #s.close()    

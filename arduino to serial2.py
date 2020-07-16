import serial
import socket
import time

#number of data points to pull before killing socket
timeout_value = 20

#because this test only implements the temperature sensor, there is no need to determine baud rates and ports
try:
    serial_1 = serial.Serial('/dev/ttyUSB0',9600) 
    assign = {"TEMP":"","GPS":"","GYRO":""}
except Exception as e:
    print(e)
    print("Check to make sure that all sensors are plugged in.")
    print("Unplug all connected devices, wait ten seconds, then replug only the sensors.")
    print("The program will exit in 30 seconds, or you can exit manually.")
    time.sleep(30)
    exit()

try:

    socket_1 = socket.socket()
    port = 12357
    socket_1.bind(('',port))#no ip is defined, so this listens to requests coming from all computers on network on this port
    print("socket bound to port %s"%(port))
    socket_1.listen(5)
    print("waiting on connection")
except Exception as e:
    print(e)

while True:
    # Establish connection with client. 
    c, addr = socket_1.accept()      
    print ('Got connection from', addr) 

    #get and send data indefinitely over the socket until timeout_value is reached
    try:  
        while True:
            base_list = []
            temp_data = str(serial_1.read_until())
            print(temp_data)
            temp_parsed = temp_data.split("|")
            print(temp_parsed)
            if len(temp_parsed) != 5:
                continue
            for i in range(2,4):
                base_list.append(temp_parsed[i])
            #c.send(send_msg.encode('utf-8'))
            #c.send(temp_data.encode('utf-8'))
            if len(base_list) > 0:
                c.send(str(base_list).encode('utf-8'))
            time.sleep(1)
    except:
        c.close()
    # Close the connection with the client 
    c.close() 
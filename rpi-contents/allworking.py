#KeyError occurred on fitbit_data_final = [str(...)]..
#introduce a check to catch this


import asyncio
import websockets
import time
import math
import serial
import socket
import ast

fitbit_port = 12345 #if the port is busy by normal means, it should clear eventually
outgoing_port = 12348
c = None
connecting = False
failed_fitbit = 0
failed_client = 11

s = None
s2 = None
s3 = None

#Initialize serial ports
try:
    assign = {"TEMP":None,"GPS":None,"DISP":None}
    s = serial.Serial('/dev/ttyUSB0',9600)
    s2 = serial.Serial('/dev/ttyUSB1',9600)
    s3 = serial.Serial('/dev/ttyUSB2',9600)
except serial.serialutil.SerialException:
    #If the above devices fail, they're NoneType
    print("Not all devices are connected. Will attempt to continue anyways.")
except Exception as e:
    print(e)
    print("Check to make sure that all sensors are plugged in.")
    print("Unplug all connected devices, wait ten seconds, then replug only the sensors.")
    print("The program will exit in 30 seconds, or you can exit manually.")
    time.sleep(30)
    exit()

time.sleep(5)
    
def determine_ports():
    print("Attempting to (re)assign ports...")
    if s != None:
        while True:
            c = str(s.read_until()).split("|")
            if len(c) < 2:
                continue
            if c[1] == "TEMP":
                assign["TEMP"] = "s"
                print("/USB0 = TEMP")
                break
            elif c[1] == "GPS":
                assign["GPS"] = "s"
                print("/USB0 = GPS")
                break
            elif c[1] == "DISP":
                assign["DISP"] = "s"
                print("/USB0 = DISP")
                break
    else:
        print("No device available at /USB0.")
    if s2 != None:
        while True:
            c = str(s2.read_until()).split("|")
            if len(c) < 2:
                continue
            if c[1] == "TEMP":
                assign["TEMP"] = "s2"
                print("/USB1 = TEMP")
                break
            elif c[1] == "GPS":
                assign["GPS"] = "s2"
                print("/USB1 = GPS")
                break
            elif c[1] == "DISP":
                assign["DISP"] = "s2"
                print("/USB1 = DISP")
                break
    else:
        print("No device available at /USB1.")
    if s3 != None:
        while True:
            c = str(s3.read_until()).split("|")
            if len(c) < 2:
                continue
            if c[1] == "TEMP":
                assign["TEMP"] = "s3"
                print("/USB2 = TEMP")
                break
            elif c[1] == "GPS":
                assign["GPS"] = "s3"
                print("/USB2 = GPS")
                break
            elif c[1] == "DISP":
                assign["DISP"] = "s3"
                print("/USB2 = DISP")
                break
    else:
        print("No device available at /USB2.")

#why this instead of the one with all the work?
#handshakes, decodes, encodes, etc are all done automatically

async def cget():
    global c
    global connecting
    global failed_client
    failed_client += 1
    c = None
    #print("a")
    #print(failed_client)
    if failed_client > 10: #retry every n reads
        #print("b")
        try:
            if not connecting:
                connecting = True
                failed_client = 0 #reset so it retries if this fails
                client_socket = socket.socket()
                client_socket.settimeout(5)#wait 5 sec max for things to happen
                port = outgoing_port
                client_socket.bind(('',port))#no ip is defined, so this listens to requests coming from all computers on network on this port
                print("socket bound to port %s"%(port))
                client_socket.listen(5)
                print("waiting on connection from receiving client")
                c, addr = client_socket.accept()
                print ('Got connection from '+str(addr))
                connecting = False
                #client_socket.settimeout(None)
        except Exception as e:
            connecting = False
            print(e)

async def handle_cdata():
    pass
    #figure out how to handle data while the client is trying to get a connection


async def hello(websocket, path):
    global c
    global failed_fitbit
    global failed_client
    print('got connection')
    if not c:
        await cget()
    while True:
        fitbitRecieved = "{}"
        sensor_data = []
        final = {"timestamp":None,"fitbit_data":{},"sensor_data":{}}
        
        temp_data = eval("str(%s.read_until())"%assign["TEMP"]) if assign["TEMP"] else "--|TEMP|--|--"
        #future: ...|DISP|instataneous pitch|roll|yaw|total_x|total_y|total vector count|this read vector_count|internal_vector_length_constant
        #calculate the resultant on the pi or receiving client, whichever turns out to be better
        disp_data = eval("str(%s.read_until())"%assign["DISP"]) if assign["DISP"] else "--|DISP|--|--|--|--|--|--|--|--"
        gps_data = eval("str(%s.read_until())"%assign["GPS"]) if assign["GPS"] else "--|GPS|--|--|--|--"
        #latitude|longitude|hdop|satellite count
        
        temp_parsed = temp_data.split("|")
        disp_parsed = disp_data.split("|")
        gps_parsed = gps_data.split("|")
        for i in range(2,4):
            sensor_data.append(temp_parsed[i])
        for i in range(2,10):
            sensor_data.append(disp_parsed[i])
        for i in range(2,6):
            sensor_data.append(gps_parsed[i])
        try:
            if len(sensor_data) > 0:
                await websocket.send(str(sensor_data))
                fitbitRecieved = await websocket.recv()
                fitbit_data = ast.literal_eval(fitbitRecieved)
                #print(fitbit_data)
                fitbit_data_final = [str(fitbit_data['hr_only']),str(fitbit_data['pressure'])]
                failed_fitbit = 0
        except:
            failed_fitbit += 1
            print("Seems the fitbit connection was lost. %s failed connections."%failed_fitbit)
        #print(f"< {fitbitRecieved}")
        #print(sensor_data)
        
        final["sensor_data"] = sensor_data
        final["fitbit_data"] = fitbit_data_final
        final["timestamp"] = math.floor(time.time())
        print(final)
        try:
            if c != None:
                print("a")
                c.send((str(final)+"|").encode('utf-8'))
            else:
                await cget()
                print("No client available... waiting on retry")
        except BrokenPipeError:
            print("Receiving client disconnected. Will retry connection. (BrokenPipeError)")
            await cget()
        except AttributeError:
            print("Receiving client disconnected. Will retry connection. (AttributeError)")
            await cget()
        except ConnectionResetError:
            print("Receiving client disconnected. Will retry connection. (ConnectionResetError)")
            await cget()
        except Exception as e:
            print("Something else happened: %s"%e)
        #await websocket.send("Hello World!")


initial_time = math.floor(time.time())
determine_ports()

start_server = websockets.serve(hello, port=fitbit_port)
print('waiting on connection from fitbit')

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()

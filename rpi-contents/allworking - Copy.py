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
fitbit_connected = False

s = None
s2 = None
s3 = None

all_sensor_data = []
all_fitbit_data = []

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
    try:
        if not connecting:
            connecting = True
            socket_1 = socket.socket()
            socket_1.setblocking(False)
            port = outgoing_port
            socket_1.bind(('',port))#no ip is defined, so this listens to requests coming from all computers on network on this port
            print("socket bound to port %s"%(port))
            socket_1.listen(5)
            print("waiting on connection from receiving client")
            c, addr = socket_1.accept()      
            print ('Got connection from '+str(addr))
            connecting = False
    except Exception as e:
        print(e)

    #figure out how to handle data while the client is trying to get a connection

async def handle_sensors():
    global all_sensor_data
    sensor_data = []
    
    temp_data = eval("str(%s.read_until())"%assign["TEMP"]) if assign["TEMP"] else "--|TEMP|--|--"
    #future: ...|DISP|instataneous pitch|roll|yaw|total_x|total_y|vector_count|internal_vector_length_constant
    #calculate the resultant on the pi or receiving client, whichever turns out to be better
    disp_data = eval("str(%s.read_until())"%assign["DISP"]) if assign["DISP"] else "--|DISP|--|--|--|--|--|--|--"
    gps_data = eval("str(%s.read_until())"%assign["GPS"]) if assign["GPS"] else "--|GPS|--|--|--|--"
    
    temp_parsed = temp_data.split("|")
    disp_parsed = disp_data.split("|")
    gps_parsed = gps_data.split("|")
    for i in range(2,4):
        sensor_data.append(temp_parsed[i])
    for i in range(2,9):
        sensor_data.append(disp_parsed[i])
    for i in range(2,6):
        sensor_data.append(gps_parsed[i])
    print(sensor_data)
    all_sensor_data.append(sensor_data)
    
async def fitbit(websocket, path):
    global failed_fitbit
    fitbitRecieved = "{}"
    fitbitRecieved = await websocket.recv()
    fitbit_data = ast.literal_eval(fitbitRecieved)
    print(fitbit_data)
    all_fitbit_data.append(fitbit_data)
    if all_sensor_data:
        try:
            await websocket.send(str(all_sensor_data[0]))
            failed_fitbit = 0
        except:
            failed_fitbit += 1
            print("Seems the fitbit connection was lost. %s failed connections."%failed_fitbit)

async def handle_fitbit():
    pass
'''
    global fitbit_connected
    if not fitbit_connected:
        start_server = websockets.serve(fitbit, port=fitbit_port)
        print('waiting on connection from fitbit')
        fitbit_connected = True
    else:
        pass
'''
async def handle_sending():

    global c
    global all_fitbit_data
    global all_sensor_data
    if c:
        if all_fitbit_data and all_sensor_data:
            try:
                go = [int(time.time()),all_fitbit_data[0],all_sensor_data[0]]
                c.send(str().encode('utf-8'))
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
    else:
        await cget()
    
async def main(websocket,path):
    #task1 = asyncio.create_task(handle_fitbit(websocket,path))
    task2 = asyncio.create_task(handle_sensors())
    task3 = asyncio.create_task(handle_sending())
    #await task1
    await task2
    await task3


initial_time = math.floor(time.time())
determine_ports()


start_server = websockets.serve(main, port=fitbit_port)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()


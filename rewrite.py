import asyncio
import websockets
import time
import math
import serial
import socket
import ast

class constants:
    pass

class states:
    s = None
    s2 = None
    s3 = None
    assignments = None

    fitbit_connection = None
    ui_connection = None

    queue = []
    fitbit_queue = []



def init_ports():
    try:
        states.assignments = {"TEMP":None,"GPS":None,"DISP":None}
        states.s = serial.Serial('/dev/ttyUSB0',9600)
        states.s2 = serial.Serial('/dev/ttyUSB1',9600)
        states.s3 = serial.Serial('/dev/ttyUSB2',9600)
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

def determine_ports():
    print("Attempting to (re)assign ports...")
    if states.s != None:
        while True:
            c = str(states.s.read_until()).split("|")
            if len(c) < 2:
                continue
            if c[1] == "TEMP":
                states.assignments["TEMP"] = "states.s"
                print("/USB0 = TEMP")
                break
            elif c[1] == "GPS":
                states.assignments["GPS"] = "states.s"
                print("/USB0 = GPS")
                break
            elif c[1] == "DISP":
                states.assignments["DISP"] = "states.s"
                print("/USB0 = DISP")
                break
    else:
        print("No device available at /USB0.")
    if states.s2 != None:
        while True:
            c = str(states.s2.read_until()).split("|")
            if len(c) < 2:
                continue
            if c[1] == "TEMP":
                states.assignments["TEMP"] = "states.s2"
                print("/USB1 = TEMP")
                break
            elif c[1] == "GPS":
                states.assignments["GPS"] = "states.s2"
                print("/USB1 = GPS")
                break
            elif c[1] == "DISP":
                states.assignments["DISP"] = "states.s2"
                print("/USB1 = DISP")
                break
    else:
        print("No device available at /USB1.")
    if states.s3 != None:
        while True:
            c = str(states.s3.read_until()).split("|")
            if len(c) < 2:
                continue
            if c[1] == "TEMP":
                states.assignments["TEMP"] = "states.s3"
                print("/USB2 = TEMP")
                break
            elif c[1] == "GPS":
                states.assignments["GPS"] = "states.s3"
                print("/USB2 = GPS")
                break
            elif c[1] == "DISP":
                states.assignments["DISP"] = "states.s3"
                print("/USB2 = DISP")
                break
    else:
        print("No device available at /USB2.")


#figure out if the connecting websocket is either the fitbit or the client, adding them to the respective pool
async def connection_handler(connection, path):
    init_msg = await connection.recv()
    if init_msg == "fitbit":
        states.fitbit_connection = connection
    elif init_msg == "ui":
        states.ui_connection = connection
    else:
        states.fitbit_connection = connection
    while True:
        #not really sure what to do here to keep the connection alive
        await asyncio.sleep(1)

async def fitbit_handler():
    while True:
        await asyncio.sleep(1)
        try:
            if states.fitbit_connection:
                fitbitRecieved = "{}"
                fitbitRecieved = await states.fitbit_connection.recv()
                print(fitbitRecieved+"> fitbit_handler")
                if not fitbitRecieved:
                    print("Connection with fitbit broken.")
                    states.fitbit_connection = None
                else:
                    fitbit_data = ast.literal_eval(fitbitRecieved)
                    fitbit_data_final = [str(fitbit_data['hr_only']),str(fitbit_data['pressure'])]
                    print(fitbit_data_final)
                    states.fitbit_queue.append(fitbit_data_final)
        except websockets.exceptions.ConnectionClosedOK:
            print("Connection with (something) broken.")
            states.fitbit_connection = None
            continue

async def data_handler():
    while True:
        await asyncio.sleep(1)  # switch to other code and continue execution in 5 seconds
        sensor_data = []
        final = {"timestamp":None,"fitbit_data":[],"sensor_data":[]}
        
        temp_data = eval("str(%s.read_until())"%states.assignments["TEMP"]) if states.assignments["TEMP"] else "--|TEMP|--|--"
        disp_data = eval("str(%s.read_until())"%states.assignments["DISP"]) if states.assignments["DISP"] else "--|DISP|--|--|--|--|--|--|--|--"
        gps_data = eval("str(%s.read_until())"%states.assignments["GPS"]) if states.assignments["GPS"] else "--|GPS|--|--|--|--"
        #latitude|longitude|hdop|satellite count
        #calculate the resultant on the pi or receiving client, whichever turns out to be better
        temp_parsed = temp_data.split("|")
        disp_parsed = disp_data.split("|")
        gps_parsed = gps_data.split("|")
        for i in range(2,4):
            sensor_data.append(temp_parsed[i])
        for i in range(2,10):
            sensor_data.append(disp_parsed[i])
        for i in range(2,6):
            sensor_data.append(gps_parsed[i])
        
        final["sensor_data"] = sensor_data
        if states.fitbit_queue:
            final["fitbit_data"] = states.fitbit_queue[0]
            del states.fitbit_queue[0]
        else:
            final["fitbit_data"] = ["--","--"]
        final["timestamp"] = math.floor(time.time())
        print(final)
        
        if states.fitbit_connection:
            try:
                to_fitbit_string = str(sensor_data)
                await states.fitbit_connection.send(to_fitbit_string)
                print(to_fitbit_string+" --> fitbit")
            except websockets.exceptions.ConnectionClosedError:
                print("Connection with fitbit broken.")
                states.fitbit_connection = None
                continue
        if states.ui_connection:
            ui_string = str(final)+"|"
            await states.ui_connection.send(ui_string)
        #start sending stuff


#https://stackoverflow.com/questions/32054066/python-how-to-run-multiple-coroutines-concurrently-using-asyncio

init_ports()
determine_ports()
start_server = websockets.serve(connection_handler, port=8765) #,ping_timeout=None
asyncio.get_event_loop().run_until_complete(start_server)
asyncio.ensure_future(data_handler())  # run the other two functions in parallel
asyncio.ensure_future(fitbit_handler())
asyncio.get_event_loop().run_forever()
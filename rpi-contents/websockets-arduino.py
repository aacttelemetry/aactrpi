import asyncio
import serial
import websockets
import time
import math

#why this instead of the one with all the work?
#handshakes, decodes, encodes, etc are all done automatically

serial_1 = serial.Serial('/dev/ttyUSB0',9600) 

#initial_time = math.floor(time.time())
async def hello(websocket, path):
    print('got connection')
    while True:
        #fitbitRecieved = await websocket.recv()
        #print(f"< {fitbitRecieved}")
        base_list = []
        temp_data = str(serial_1.read_until())
        print(temp_data)
        temp_parsed = temp_data.split("|")
        print(temp_parsed)
        if len(temp_parsed) != 5:
            continue
        for i in range(2,4):
            base_list.append(temp_parsed[i])
        await websocket.send(base_list)
        #await websocket.send("Hello World!")

 
start_server = websockets.serve(hello, port=12390)
print('waiting on connection')

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()

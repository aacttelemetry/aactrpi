import asyncio
import websockets
import time
import math

#why this instead of the one with all the work?
#handshakes, decodes, encodes, etc are all done automatically

initial_time = math.floor(time.time())
async def hello(websocket, path):
    print('got connection')
    while True:
        fitbitRecieved = await websocket.recv()
        print(f"< {fitbitRecieved}")
        await websocket.send(str(initial_time - math.floor(time.time())))
        #await websocket.send("Hello World!")

 
start_server = websockets.serve(hello, port=12345)
print('waiting on connection')

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()

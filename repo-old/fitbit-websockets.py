import asyncio
import websockets
 
async def hello(websocket, path):
    while True:
        fitbitRecieved = await websocket.recv()
        print(f"< {fitbitRecieved}")
        await websocket.send("Hello World!")

    await websocket.send("Hello World!")
 
start_server = websockets.serve(hello, port=12345)
 
asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()

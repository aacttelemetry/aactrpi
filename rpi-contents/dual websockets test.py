import asyncio
import websockets

async def echo(websocket, path):
    await websocket.send("hello")

start_server = websockets.serve(echo, port=8765)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
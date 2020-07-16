import asyncio

import websockets

# here we'll store all active connections to use for sending periodic messages
connections = []

#https://stackoverflow.com/questions/32054066/python-how-to-run-multiple-coroutines-concurrently-using-asyncio

async def connection_handler(connection, path):
    print("got connection")
    connections.append(connection)  # add connection to pool
    while True:
        try:
            msg = await connection.recv()
            if msg is None:  # connection lost
                connections.remove(connection)  # remove connection from pool, when client disconnects
                break
            else:
                print('< {}'.format(msg))
            await connection.send(msg)
            print('> {}'.format(msg))
        except websockets.exceptions.ConnectionClosedOK:
            connections.remove(connection)
            break

async def send_periodically():
    while True:
        try:
            await asyncio.sleep(5)  # switch to other code and continue execution in 5 seconds
            if not connections:
                print('offline event 1 occurred')
            for connection in connections:
                print('> Periodic event happened.')
                await connection.send('Periodic event happened.')  # send message to each connected client
        except websockets.exceptions.ConnectionClosedOK:
            continue
            
async def send_periodically2():
    while True:
        try:
            await asyncio.sleep(8)  # switch to other code and continue execution in 5 seconds
            if not connections:
                print('offline event 2 occurred')
            for connection in connections:
                print('> Periodic event 2 happened.')
                await connection.send('Periodic event 2 happened.')  # send message to each connected client
        except websockets.exceptions.ConnectionClosedOK:
            continue


start_server = websockets.serve(connection_handler, 'localhost', 8765)
asyncio.get_event_loop().run_until_complete(start_server)
asyncio.ensure_future(send_periodically())  # before blocking call we schedule our coroutine for sending periodic messages
asyncio.ensure_future(send_periodically2())
asyncio.get_event_loop().run_forever()

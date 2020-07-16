#!/usr/bin/env python3

'''
import socket

HOST = '127.0.0.1'  # Standard loopback interface address (localhost)
PORT = 65432        # Port to listen on (non-privileged ports are > 1023)

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen()
    conn, addr = s.accept()
    with conn:
        print('Connected by', addr)
        while True:
            data = conn.recv(1024)
            if not data:
                break
            conn.sendall(data)
'''


# first of all import the socket library 
import socket                
import time
import hashlib, base64
import os
import array
import six
import struct
import zlib
#https://stackoverflow.com/questions/35977916/generate-sec-websocket-accept-from-sec-websocket-key
#https://gist.github.com/joncardasis/cc67cfb160fa61a0457d6951eff2aeae
#https://stackoverflow.com/questions/18240358/html5-websocket-connecting-to-python
#many mozilla pages about html headers, including Connection, Upgrade
def make_sec_header(response):
   try:
      retu = response.split("Sec-WebSocket-Key: ")
      parsed_key = retu[1][0:24]
      #parsed_key = 'dGhlIHNhbXBsZSBub25jZQ=='
      second = (("%s258EAFA5-E914-47DA-95CA-C5AB0DC85B11"%parsed_key)).encode("utf-8")
      third = hashlib.sha1(second)
      fourth = base64.b64encode(third.digest())
      fifth = fourth.decode('utf-8')
      print("got to header")
      header = ("HTTP/1.1 101 Switching Protocols\r\n" +
      "Upgrade: websocket\r\n" +
      "Connection: Upgrade\r\n" +
      "Sec-WebSocket-Accept: %s\r\n\r\n"%fifth)
      print(header)
      header_new = header.encode("utf-8")
      return header_new
   except Exception as e:
      print(e)

#Code below is from https://stackoverflow.com/questions/43748377/sending-receiving-websocket-message-over-python-socket-websocket-client
OPCODE_TEXT = 0x1

try:
    # If wsaccel is available we use compiled routines to mask data.
    from wsaccel.xormask import XorMaskerSimple

    def _mask(_m, _d):
        return XorMaskerSimple(_m).process(_d)
except ImportError:
    # wsaccel is not available, we rely on python implementations.
    def _mask(_m, _d):
        for i in range(len(_d)):
            _d[i] ^= _m[i % 4]

        if six.PY3:
            return _d.tobytes()
        else:
            return _d.tostring()


def get_masked(data):
    mask_key = os.urandom(4)
    if data is None:
        data = ""

    bin_mask_key = mask_key
    if isinstance(mask_key, six.text_type):
        bin_mask_key = six.b(mask_key)

    if isinstance(data, six.text_type):
        data = six.b(data)

    _m = array.array("B", bin_mask_key)
    _d = array.array("B", data)
    s = _mask(_m, _d)

    if isinstance(mask_key, six.text_type):
        mask_key = mask_key.encode('utf-8')
    return mask_key + s


def ws_encode(data="", opcode=OPCODE_TEXT, mask=1):
    if opcode == OPCODE_TEXT and isinstance(data, six.text_type):
        data = data.encode('utf-8')

    length = len(data)
    fin, rsv1, rsv2, rsv3, opcode = 1, 0, 0, 0, opcode

    frame_header = chr(fin << 7 | rsv1 << 6 | rsv2 << 5 | rsv3 << 4 | opcode)

    if length < 0x7e:
        frame_header += chr(mask << 7 | length)
        frame_header = six.b(frame_header)
    elif length < 1 << 16:
        frame_header += chr(mask << 7 | 0x7e)
        frame_header = six.b(frame_header)
        frame_header += struct.pack("!H", length)
    else:
        frame_header += chr(mask << 7 | 0x7f)
        frame_header = six.b(frame_header)
        frame_header += struct.pack("!Q", length)

    if not mask:
        return frame_header + data
    return frame_header + get_masked(data)


def ws_decode(data):
    """
    ws frame decode.
    :param data:
    :return:
    """
    _data = [ord(character) for character in data]
    length = _data[1] & 127
    index = 2
    if length < 126:
        index = 2
    if length == 126:
        index = 4
    elif length == 127:
        index = 10
    return array.array('B', _data[index:]).tostring()

#sock.sendall(ws_encode(data='Hello, China!', opcode=OPCODE_TEXT))
#response = ws_decode(sock.recv(1024))

#from https://stackoverflow.com/questions/1089662/python-inflate-and-deflate-implementations

def inflate( b64string ):
    decoded_data = base64.b64decode( b64string )
    return zlib.decompress( decoded_data , -15)

# next create a socket object 
s = socket.socket()          
print("Socket successfully created")
  
# reserve a port on your computer in our 
# case it is 12345 but it can be anything 
port = 12345                
  
# Next bind to the port 
# we have not typed any ip in the ip field 
# instead we have inputted an empty string 
# this makes the server listen to requests  
# coming from other computers on the network 
s.bind(('', port))         
print ("socket binded to %s" %(port))
  
# put the socket into listening mode 
s.listen(5)      
print ("socket is listening")   

# a forever loop until we interrupt it or  
# an error occurs 
while True: 
  
   # Establish connection with client. 
   c, addr = s.accept()      
   print ('Got connection from', addr)
   #print(c.recv(1024))
   response = c.recv(1024).decode('utf-8')
   print(response)
   c.send(make_sec_header(response))
   while True:
      got = c.recv(1024)
      print(got.decode('cp1252','replace'))
      #print(inflate(got))
      #print(ws_decode(got))
   '''
   while True:
      send_msg = input("Send ('break' to break): ")
   # send a thank you message to the client.
      if send_msg == 'break':
         break
      else:
         c.send(send_msg.encode('utf-8'))
   '''
   '''
   pi_ip = '192.168.1.65'
  
   # Create a socket object 
   sh = socket.socket()          
     
   # Define the port on which you want to connect 
   port = 12345               
     
   # connect to the pi
   sh.connect((pi_ip, port))
   '''
   '''
   c.send(make_header())
   while True:
      send_msg = input("Send ('break' to break): ")
   # send a thank you message to the client.
      if send_msg == 'break':
         break
      else:
         c.send(send_msg.encode('utf-8'))
   # Close the connection with the client
   c.close()
   
   #temp_list = (s.recv(1024).decode("utf-8"))
   #print(temp_list)
   '''

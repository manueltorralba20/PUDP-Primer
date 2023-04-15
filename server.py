#! /usr/bin/env python

# Server for PUDP server.
#
# Usage: server [port]            (to start a server)

import pyuv
import signal
import sys
import struct
from socket import *

ECHO_PORT = 50000 + 7
BUFSIZE = 1024

# Arbitrary session id TODO, this should be dynamic per connection
SESSION_ID = 25

# Header/protocol constants
HEADER_LENGTH = 12

# Index for message type/command in header
COMMAND_INDEX = 2

# Codes for types of messages/commands
HELLO_CODE = 0
DATA_CODE = 1
ALIVE_CODE = 2
GOODBYE_CODE = 3

users = {}

def main():
    # if len(sys.argv) > 2:
    #     usage()
    server()


def usage():
    sys.stdout = sys.stderr  # TODO why ?
    print('Usage: server [port]            (server)')
    sys.exit(2)


def pack(command, seq, sessionID):
    return struct.pack('!HBBII', 0xC356, 1, command, seq, sessionID)


def unpack(data):
    return struct.unpack('!HBBII', data)

def bye_print(header):
    print(f'{header[4]} Session closed')

def debug_print(header, data):
    statement = {
        HELLO_CODE: 'Session created',
        DATA_CODE: data,
        GOODBYE_CODE: f'GOODBYE from client.',
    }
    print(f'{header[4]} [{header[3]}] {statement.get(header[2])}')

def make_packet(header, data):
    command_coder = {
        HELLO_CODE: HELLO_CODE,
        DATA_CODE: ALIVE_CODE,
        GOODBYE_CODE: GOODBYE_CODE,
    }
    new_header = pack(command_coder.get(header[2]), header[3], header[4])
    return new_header + ''.encode('utf-8')

def on_read(handle, ip_port, flags, raw_data, error):
    
    if raw_data is not None:
        header = unpack(raw_data[:HEADER_LENGTH])
        data = raw_data[HEADER_LENGTH:].decode('utf-8')
        
        # print(f'handle = {handle}')
        # print(f'ip_port = {ip_port}')
        # print(f'raw_data = {raw_data}')
        # print(f'type of raw_data = {type(raw_data)}')
        # print(f'header = {header}')
        # print(f'data unpacked = {data}')
        # print()
        # print(f'header[0] = {header[0]}')
        if header[0] == 50006:
            if header[2]==HELLO_CODE and header[4] not in users.keys():
                debug_print(header, data)
                users[header[4]] = header[3]
                new_packet = make_packet(header, data)
                handle.send(ip_port, new_packet)
            elif header[2]==DATA_CODE:
                debug_print(header, data)
                users[header[4]] = header[3]
                new_packet = make_packet(header, data)
                handle.send(ip_port, new_packet)
            elif header[2]==GOODBYE_CODE:
                debug_print(header, data)
                users.pop(header[4])
                new_packet = make_packet(header, data)
                handle.send(ip_port, new_packet)
            else:
                users.pop(header[4])
                bye_print(header)
           


def handle_keyboard_input(tty_handle, data, error):
    # your code here for keyboard input
    if data=='q':
        for user in users.keys():
            print(f'{user} Session closed')
            # tty_handle.send(ip_port, pack(3, users[user], user)+''.encode('utf-8'))
            users.pop(user)
    
def server():
    # Get port number
    if len(sys.argv) == 2:
        port = eval(sys.argv[1])
    else:
        port = ECHO_PORT

    print(f'Waiting on port {port}...')


    loop = pyuv.Loop.default_loop()
    server = pyuv.UDP(loop)
    server.bind(("0.0.0.0", port))
    server.start_recv(on_read)
    serverTTY = pyuv.TTY(loop, sys.stdin.fileno(), True)
    serverTTY.start_read(handle_keyboard_input)

    loop.run()

    print("Stopped!")


if __name__ == '__main__':
    main()

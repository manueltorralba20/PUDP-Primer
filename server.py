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
    print(f'len of data = {len(data)}')
    return struct.unpack('!HBBII', data)

def debug_print(header, data):
    statement = {
        0: 'Session created',
        1: data,
        3: f'GOODBYE from client.\n{header[4]} Session closed',
    }
    print(f'{header[4]} [{header[3]}] {statement.get(header[2], header[2])}')

def make_packet(header, data):
    command_coder = {
        HELLO_CODE: HELLO_CODE,
        DATA_CODE: ALIVE_CODE,
        GOODBYE_CODE: GOODBYE_CODE,
    }
    new_header = pack(command_coder.get(header[2]), header[3], header[4])
    return new_header + data.encode('utf-8')
    pass

def on_read(handle, ip_port, flags, raw_data, error):
    
    if raw_data is not None:
        header = unpack(raw_data[:HEADER_LENGTH])
        data = raw_data[HEADER_LENGTH:].decode('utf-8')  # TODO get rid of? unused
        debug_print(header, data)
        print(f'handle = {handle}')
        print(f'ip_port = {ip_port}')
        print(f'raw_data = {raw_data}')
        print(f'type of raw_data = {type(raw_data)}')
        # print(f'data unpacked = {unpack(raw_data)}')
        print(f'header = {header}')
        print(f'data unpacked = {data}')
        print()

        new_packet = make_packet(header, data)
        handle.send(ip_port, new_packet)#TODO HUMBERTO FIX THIS

def signal_cb(handle, signum):
    # signal_h.close()
    # server.close()
    pass

def server():
    # Get port number
    print(f'sys.argv = {sys.argv}')
    print(f'length of sys.argv = {len(sys.argv)}')
    if len(sys.argv) == 2:
        port = eval(sys.argv[1])
    else:
        port = ECHO_PORT

    print(f'Waiting on port {port}...')


    loop = pyuv.Loop.default_loop()
    server = pyuv.UDP(loop)
    server.bind(("0.0.0.0", port))
    server.start_recv(on_read)

    # signal_h = pyuv.Signal(loop)
    # signal_h.start(signal_cb, signal.SIGINT)

    loop.run()

    print("Stopped!")

    # # Setup socket
    # s = socket(AF_INET, SOCK_DGRAM)
    # s.bind(('', port))
    # seq_number = 0
    # print('Pudp echo server ready')

    # # Does not handle/store server state
    # while 1:
    #     # Unpack and read
    #     rcv_msg, addr = s.recvfrom(BUFSIZE)
    #     header = unpack(rcv_msg[:HEADER_LENGTH])
    #     data = rcv_msg[HEADER_LENGTH:].decode('utf-8')
    #     print('server received %r from %r' % (data, addr))

    #     # Act according to command code received
    #     # Note: ALIVE messages and invalid command codes are ignored
    #     if header[COMMAND_INDEX] == HELLO_CODE:
    #         # pack and send
    #         header = pack(header[COMMAND_INDEX], seq_number, SESSION_ID)
    #         data_msg = header + ''.encode('utf-8')
    #         s.sendto(data_msg, addr)
    #         seq_number += 1

    #     elif header[COMMAND_INDEX] == DATA_CODE:
    #         # pack and send
    #         header = pack(ALIVE_CODE, seq_number, SESSION_ID)
    #         data_msg = header + ''.encode('utf-8')
    #         s.sendto(data_msg, addr)
    #         seq_number += 1

    #     elif header[COMMAND_INDEX] == GOODBYE_CODE:
    #         header = pack(header[COMMAND_INDEX], seq_number, SESSION_ID)
    #         data_msg = header + ''.encode('utf-8')
    #         s.sendto(data_msg, addr)
    #         seq_number += 1
    #         break

    # # Terminate socket
    # s.close()


if __name__ == '__main__':
    main()

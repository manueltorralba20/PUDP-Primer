#! /usr/bin/env python

# Server for PUDP server.
#
# Usage: server [port]            (to start a server)

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
    if len(sys.argv) > 2:
        usage()
    server()


def usage():
    sys.stdout = sys.stderr  # TODO why ?
    print('Usage: server [port]            (server)')
    sys.exit(2)


def pack(command, seq, sessionID):
    return struct.pack('!HBBII', 0xC356, 1, command, seq, sessionID)


def unpack(data):
    return struct.unpack('!HBBII', data)


def server():
    # Get port number
    if len(sys.argv) > 1:
        port = eval(sys.argv[2])
    else:
        port = ECHO_PORT

    # Setup socket
    s = socket(AF_INET, SOCK_DGRAM)
    s.bind(('', port))
    seq_number = 0
    print('Pudp echo server ready')

    while 1:
        # Unpack and read
        rcv_msg, addr = s.recvfrom(BUFSIZE)
        header = unpack(rcv_msg[:HEADER_LENGTH])
        data = rcv_msg[HEADER_LENGTH:].decode('utf-8')
        print('server received %r from %r' % (data, addr))

        # Act according to command code received
        # Note: ALIVE messages are ignored
        if header[COMMAND_INDEX] == HELLO_CODE:
            # pack and send
            header = pack(header[COMMAND_INDEX], seq_number, SESSION_ID)
            data_msg = header + ''.encode('utf-8')
            s.sendto(data_msg, addr)
            seq_number += 1

        elif header[COMMAND_INDEX] == DATA_CODE:
            # pack and send
            header = pack(ALIVE_CODE, seq_number, SESSION_ID)
            data_msg = header + ''.encode('utf-8')
            s.sendto(data_msg, addr)
            seq_number += 1

        elif header[COMMAND_INDEX] == GOODBYE_CODE:
            header = pack(header[COMMAND_INDEX], seq_number, SESSION_ID)
            data_msg = header + ''.encode('utf-8')
            s.sendto(data_msg, addr)
            seq_number += 1
            break

    # Terminate socket
    s.close()


if __name__ == '__main__':
    main()

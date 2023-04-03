#! /usr/bin/env python TODO what is this?

# Client for PUDP client.
#
# Usage:    client host [port] <file (client)

import sys
import struct
from socket import *

ECHO_PORT = 50000 + 7
BUFSIZE = 1024

# Arbitrary session id TODO, this should be updated based on server
SESSION_ID = 25

# Header/protocol constants
HEADER_LENGTH = 12

# Codes for types of messages/commands
HELLO_CODE = 0
DATA_CODE = 1
ALIVE_CODE = 2
GOODBYE_CODE = 3

# Index for message type/command in header
COMMAND_INDEX = 2


def main():
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        usage()
    client()


def usage():
    sys.stdout = sys.stderr
    print('Usage:   client host [port] <file (client)')
    sys.exit(2)


def pack(command, seq, sessionID):
    return struct.pack('!HBBII', 0xC356, 1, command, seq, sessionID)


def unpack(data):
    return struct.unpack('!HBBII', data)


def client():
    # Get host and port
    host = sys.argv[1]
    if len(sys.argv) > 2:
        port = eval(sys.argv[2])  # TODO use something other than eval()?
    else:
        port = ECHO_PORT

    # Setup socket
    addr = host, port
    s = socket(AF_INET, SOCK_DGRAM)
    s.bind(('', 0))
    print('PUDP echo client ready, reading stdin')
    seq_number = 0

    # pack and send HELLO message to server
    header = pack(HELLO_CODE, seq_number, SESSION_ID)
    data_msg = header + ''.encode('utf-8')
    s.sendto(data_msg, addr)
    seq_number += 1

    # wait for HELLO back, unpack read stuff
    # Fencepost for checking receiving messages
    rcv_msg, addr = s.recvfrom(BUFSIZE)
    header = unpack(rcv_msg[:HEADER_LENGTH])
    data = rcv_msg[HEADER_LENGTH:].decode('utf-8')  # TODO get rid of? unused

    while header[COMMAND_INDEX] != HELLO_CODE:
        rcv_msg, addr = s.recvfrom(BUFSIZE)
        header = unpack(rcv_msg[:HEADER_LENGTH])
        data = rcv_msg[HEADER_LENGTH:].decode('utf-8')  # TODO get rid? unused
        seq_number += 1

    # Input mode!
    while 1:
        line = sys.stdin.readline()
        if not line or line == 'q\n':  # TODO piazza, strip(line) == 'q' ?
            break

        # Pack and send client data
        header = pack(DATA_CODE, seq_number, SESSION_ID)
        data_msg = header + line.encode('utf-8')
        s.sendto(data_msg, addr)
        seq_number += 1

        # TODO no timer/ checks for ALIVE yet

    # All done, send goodbye and terminate
    header = pack(GOODBYE_CODE, seq_number, SESSION_ID)
    data_msg = header + ''.encode('utf-8')
    s.sendto(data_msg, addr)
    seq_number += 1


if __name__ == '__main__':
    main()

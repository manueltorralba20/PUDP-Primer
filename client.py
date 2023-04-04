#! /usr/bin/env python TODO what is this?

# Client for PUDP client.
#
# Usage:    client host [port] <file (client)

import random
import sys
import struct
from socket import *

ECHO_PORT = 50000 + 7
BUFSIZE = 1024

# Client generates random session ID
SESSION_ID = random.getrandbits(32)

# Header/protocol constants
HEADER_LENGTH = 12
VERSION_NUMBER = 1

# Index for message type/command in header
COMMAND_INDEX = 2

# Codes for types of messages/commands
HELLO_CODE = 0
DATA_CODE = 1
ALIVE_CODE = 2
GOODBYE_CODE = 3


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


def get_msg(recv_socket):
    # Wait and get message
    rcv_msg, addr = recv_socket.recvfrom(BUFSIZE)

    # Length check
    if len(rcv_msg) < HEADER_LENGTH:
        return None, None

    header = unpack(rcv_msg[:HEADER_LENGTH])
    data = rcv_msg[HEADER_LENGTH:].decode('utf-8')  # TODO get rid of? unused

    # Check if valid message TODO constant 0xC356
    if(header[0] != 0xC356 or header[1] != VERSION_NUMBER
            or header[COMMAND_INDEX] < HELLO_CODE
            or header[COMMAND_INDEX] > GOODBYE_CODE):
        return None, None

    return header, data


# Sends goodbye to send_socket at the current seq_number
def send_goodbye(send_socket, seq_number):
    header = pack(GOODBYE_CODE, seq_number, SESSION_ID)
    data_msg = header + ''.encode('utf-8')
    send_socket.sendto(data_msg, addr)


# TODO add threads (one for waiting for stdin, another for waiting on receiving
# messages
# TODO Implement ignoring certain messages, wrong header fields
# TODO Follow all guidelines from in-class exercise (18 questions/edge cases)
# TODO Implement timer!
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
    # rcv_msg, addr = s.recvfrom(BUFSIZE)
    # header = unpack(rcv_msg[:HEADER_LENGTH])
    # data = rcv_msg[HEADER_LENGTH:].decode('utf-8')  # TODO get rid of? unused

    header, data = get_msg(s)
    while header is None or header[COMMAND_INDEX] != HELLO_CODE:
        header, data = get_msg(s)
        # rcv_msg, addr = s.recvfrom(BUFSIZE)
        # header = unpack(rcv_msg[:HEADER_LENGTH])
        # data = rcv_msg[HEADER_LENGTH:].decode('utf-8')  # TODO get rid? unused


    # Input mode! TODO start unique thread here
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
    send_goodbye(s, seq_number)
    seq_number += 1


if __name__ == '__main__':
    main()

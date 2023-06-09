#! /usr/bin/env python

# Client for PUDP client.
#
# Usage:    client host [port] <file (client)

import random
import sys
import struct
import threading
import time
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

# Timer (thread waiting on timer) to be used in input-listening thread and
# socket-listening thread
t3 = None

# State check for timer, will only be used to distinguish from Ready state and
# Ready Timer state
is_ready_state = True

# Used for communicating a TIMEOUT
has_timeout = False

# seq_number does not need to
seq_number = 0

final_lock = None


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
    if (header[0] != 0xC356 or header[1] != VERSION_NUMBER
            or header[COMMAND_INDEX] < HELLO_CODE
            or header[COMMAND_INDEX] > GOODBYE_CODE):
        return None, None

    if header[COMMAND_INDEX] == DATA_CODE or header[4] != SESSION_ID:
        # Send goodbye and close
        # print(f'header[4] = {header[4]}')
        # print(f'session_id {SESSION_ID}')
        # print(f'header[1] = {header[1]}')
        # print(f'data-code = {DATA_CODE}')
        global t3
        t3 = threading.Timer(0, handle_timeout, [recv_socket, addr])
        t3.start()

    if header[1] == GOODBYE_CODE:
        # CLOSE
        global has_timeout
        has_timeout = True
        global final_lock
        final_lock.release()

    return header, data


def handle_input(my_socket, addr):
    # print('handle_input()')
    # Fencepost so the has_timeout check can be one place (while conditional)
    global seq_number
    global t3
    global has_timeout
    line = sys.stdin.readline()
    was_eof = False
    while not has_timeout:
        if not line or line == 'q\n':  # TODO piazza, strip(line) == 'q' ?
            was_eof = True
            has_timeout = True
            break
        else:
            # No timeout :D send the data using send method? or make timeout
            # thread here?
            # Pack and send client data
            header = pack(DATA_CODE, seq_number, SESSION_ID)
            data_msg = header + line.encode('utf-8')
            my_socket.sendto(data_msg, addr)
            seq_number += 1

            # TODO add lock for this ?
            # lock.acquire()
            global is_ready_state
            if is_ready_state:
                # print('start')
                is_ready_state = False
                t3.start()
            # lock.release()

        # TODO file redirection check client.py < file.txt
        line = sys.stdin.readline()

    # Timeout or EOF occurred! TODO
    # Timeout handler should handle this TODO

    if was_eof:
        t3 = threading.Timer(0, handle_timeout, [my_socket, addr])
        t3.start()


def handle_socket(my_socket, addr):
    global has_timeout
    # Listen for ALIVE messages and update timer and is_ready_state accordingly
    # TODO currently ignoring all messages except ALIVE ones
    while not has_timeout:
        header, data = get_msg(my_socket)
        while header is None or header[COMMAND_INDEX] != ALIVE_CODE:
            header, data = get_msg(my_socket)

        global is_ready_state
        global t3
        if not is_ready_state:
            is_ready_state = True
            t3.cancel()
            t3 = threading.Timer(3, handle_timeout, [my_socket, addr])


def handle_timeout(my_socket, addr):
    global has_timeout
    has_timeout = True
    global final_lock
    final_lock.release()
    send_goodbye(my_socket, addr)


# Sends goodbye to send_socket at the current seq_number
def send_goodbye(send_socket, addr):
    global seq_number
    header = pack(GOODBYE_CODE, seq_number, SESSION_ID)
    data_msg = header + ''.encode('utf-8')
    send_socket.sendto(data_msg, addr)
    seq_number += 1

    # Basically wait 3 seconds before exiting
    time.sleep(3)


def client():
    # Get host and port
    host = sys.argv[1]
    if len(sys.argv) > 2:
        port = eval(sys.argv[2])
    else:
        port = ECHO_PORT

    # Setup socket
    addr = host, port
    s = socket(AF_INET, SOCK_DGRAM)
    s.bind(('', 0))

    global seq_number
    seq_number = 0

    # Pack and send HELLO message to server
    header = pack(HELLO_CODE, seq_number, SESSION_ID)
    data_msg = header + ''.encode('utf-8')
    s.sendto(data_msg, addr)
    seq_number += 1

    global final_lock
    final_lock = threading.Lock()
    final_lock.acquire()

    # Wait for HELLO back, unpack read stuff
    # Fencepost for checking receiving messages
    # TODO check for wrong session ID, ignore as well ?
    header, data = get_msg(s)
    while header is None and header[COMMAND_INDEX] != HELLO_CODE:
        header, data = get_msg(s)

    global t3
    t3 = threading.Timer(3, handle_timeout, [s, addr])


    # This running thread (the socket listening thread) is t0
    t1 = threading.Thread(target=handle_socket, args=[s, addr], daemon=True)
    t2 = threading.Thread(target=handle_input, args=[s, addr], daemon=True)
    t1.start()
    t2.start()

    final_lock.acquire()


if __name__ == '__main__':
    main()

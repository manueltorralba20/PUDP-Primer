#! /usr/bin/env python

# Client and server for udp (datagram) echo.
#
# Usage: udpecho -s [port]            (to start a server)
# or:    udpecho -c host [port] <file (client)

import sys
import struct
from socket import *

ECHO_PORT = 50000 + 7
BUFSIZE = 1024

SESSION_ID = 25


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
    host = sys.argv[1]
    if len(sys.argv) > 2:
        port = eval(sys.argv[2]) # TODO use something other than eval()?
    else:
        port = ECHO_PORT

    addr = host, port
    s = socket(AF_INET, SOCK_DGRAM)
    s.bind(('', 0))
    print('udp echo client ready, reading stdin')
    seq_number = 0

    # pack and send
    header = pack(0, seq_number, SESSION_ID)
    # data_msg = header + data.encode('utf-8')
    data_msg = header + ''.encode('utf-8')
    s.sendto(data_msg, addr)
    seq_number += 1

    # wait for hello back
    # unpack read stuff
    rcv_msg, addr = s.recvfrom(BUFSIZE)
    header = unpack(
        rcv_msg[
        :12])  # int(header[0]) will be 0xC356, int(header[2***]) will be 1 if this was DATA packet, etc
    data = rcv_msg[12:].decode(
        'utf-8')  # this has sequence number and session id

    while header[2] != 0:
        # print('BEFORE')
        rcv_msg, addr = s.recvfrom(BUFSIZE)
        # print('AFTER')
        header = unpack(
            rcv_msg[
            :12])  # int(header[0]) will be 0xC356, int(header[2***]) will be 1 if this was DATA packet, etc
        data = rcv_msg[12:].decode(
            'utf-8')  # this has sequence number and session id
        seq_number += 1

    while 1:
        # print('inside client while')
        line = sys.stdin.readline()
        if not line or line == 'q\n':
            break
        # pack and send
        header = pack(1, seq_number, SESSION_ID)
        # data_msg = header + data.encode('utf-8')
        data_msg = header + line.encode('utf-8')
        s.sendto(data_msg, addr)
        seq_number += 1
        print('client received %r from %r' % (data, addr))
    header = pack(3, seq_number, SESSION_ID)
    # data_msg = header + data.encode('utf-8')
    data_msg = header + ''.encode('utf-8')
    s.sendto(data_msg, addr)
    seq_number += 1


if __name__ == '__main__':
    main()
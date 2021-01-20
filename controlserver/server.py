import os
import sys
import socket
import struct
import time
import signal
import argparse

from threading import Thread, get_ident
from socketserver import (
    BaseServer,
    BaseRequestHandler,
    UDPServer,
    UnixStreamServer,
    StreamRequestHandler,
    ThreadingMixIn,
)
from enum import IntEnum

from cmd import Cmd


VERSION = '0.1'
SERVER_HOST = '0.0.0.0'
SERVER_PORT = 10000
SERVER_ID = 0

CONSOLE_SOCK = '/tmp/console.sock'

BUFFER_SIZE = 1024
CLEANUP_INTERNVAL = 10
REMOTE_LIFETIME_MAX = 10

# 48 bytes max size
# 8B |  2B | 38B
# --------------
# ID | CMD | MSG
HEADER_FMT = '!QH38s'
# 38B bytes max size
# 2B |  36B
# --------------
# STATE | MSG
MSG_FMT = '!H36s'

DEBUG=True
def dbgprint(args):
    if DEBUG:
        print(args)


class EMsgType(IntEnum):
    PING = 0
    JOB_OFFER = 1

class ERemoteState(IntEnum):
    IDLE = 0
    WORKING = 1
    ERROR = 2


class ControlServerRemoteHandler(BaseRequestHandler):
    """Handle incomming communication with remote"""

    def handle(self):
        data = self.request[0].strip()
        socket = self.request[1]

        id, cmd, msg = struct.unpack(HEADER_FMT, data)
        if cmd == EMsgType.PING:
            # unpack and decode msg part of custom dgram
            state, desc = struct.unpack(MSG_FMT, msg)
            self.server.add_remote(id, self.client_address[0], self.client_address[1], state)

            desc_decoded = desc.decode('utf-8')
            if state == ERemoteState.IDLE:
                pass
            elif state == ERemoteState.WORKING:
                pass

            dbgprint(f"Remote state {ERemoteState(state).name} || desc: {desc_decoded}")
            # sent same data back to client in uppercase
            socket.sendto(data.upper(), self.client_address)
        else:
            dbgprint(f"Received cmd {EMsgType(cmd)}, remote should PING only")


class ControlServer(ThreadingMixIn, UDPServer):

    remotes = {}
    last_cleanup = time.time()
    last_test_send = time.time()

    def __init__(self, server_address, RequestHandlerClass, bind_and_activate=True):
        UDPServer.__init__(self, server_address, RequestHandlerClass, bind_and_activate)

        self.console = None

    def add_remote(self, id, addr, port, state):
        """Adds or updates the remote"""

        if not self.remote_exist(id):
            self.remotes[id] = {}
            self.remotes[id]['addr'] = addr
            self.remotes[id]['port'] = port
            self.remotes[id]['state'] = state
            self.remotes[id]['last_seen'] = time.time()
            dbgprint(f'Adding remote: {id}')

        else:
            self.remotes[id]['addr'] = addr
            self.remotes[id]['port'] = port
            self.remotes[id]['state'] = state
            self.remotes[id]['last_seen'] = time.time()
            dbgprint(f'Updating remote: {id}')

    def remove_remote(self, id):
        if self.remote_exist(id):
            dbgprint(f'Removing stale remote: {id}')
            del self.remotes[id]

    def cleanup_remotes(self):
        """cleanup stale clients in defined interval"""

        if time.time() - self.last_cleanup > CLEANUP_INTERNVAL:
            if len(self.remotes) > 0:
                for remote in self.remotes.copy():
                    if time.time() - self.remotes[remote]['last_seen'] > REMOTE_LIFETIME_MAX:
                        self.remove_remote(remote)

            # update cleanup timer
            self.last_cleanup = time.time()

    def remote_exist(self, id) -> bool:
        return True if id in self.remotes else False

    def is_remote_alive(self, id) -> bool:
        if self.remote_exist(id):
            return True if (time.time() - self.remotes[id]['last_seen'] < REMOTE_LIFETIME_MAX) else False

    def is_remote_idle(self, id) -> bool:
        if self.remote_exist(id):
            return self.remotes[id]['state'] == ERemoteState.IDLE

    def service_actions(self):
        self.cleanup_remotes()

        # just testing communication sent to client in 1 s interval
        if time.time() - self.last_test_send > 1:
            if self.is_remote_alive(173683416947055) and self.is_remote_idle(173683416947055):
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                pack = struct.pack(HEADER_FMT, SERVER_ID, EMsgType.JOB_OFFER, "Job offer from server".encode('utf-8'))
                sock.sendto(pack, (self.remotes[173683416947055]['addr'], self.remotes[173683416947055]['port']))
                sock.close()
            self.last_test_send = time.time()

    def server_activate(self):
        pass


def signal_handler(signalNumber, frame):
    raise ExitApp

class ExitApp(Exception):
    pass


if __name__ == '__main__':

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    # Arguments parser
    ap = argparse.ArgumentParser()
    ap.add_argument("-H", "--host", action='store', type=str, default=SERVER_HOST, help=f"Control server host [{SERVER_HOST}]")
    ap.add_argument("-p", "--port", action='store', type=int, default=SERVER_PORT, help=f"Control server port [{SERVER_PORT}]")
    args = vars(ap.parse_args())

    server = ControlServer((args['host'], args['port']), ControlServerRemoteHandler)
    try:
        server.serve_forever()
    except ExitApp:
        # close & cleanup
        server.shutdown()
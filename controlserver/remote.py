import sys
import signal
import string
import socket
import struct
import time
import random
import uuid
import argparse

from threading import Thread, Event, Timer

HOST = '127.0.0.1'
PORT = 10000

PING_INTERVAL = 3
BUFFER_SIZE = 48

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

IDLE=0
WORKING=1
ERROR=2

def generate_rnd_msg() -> str:
    """generate random msg with varible lenght"""

    char_num = random.randint(8,20)
    i = 0
    s = ""
    for n in range(char_num):
        if i == char_num:
            break
        rnd_char = random.randint(0, len(string.ascii_lowercase) - 1)
        s += string.ascii_lowercase[rnd_char]
        i += 1

    return s


class Remote():

    def __init__(self, host, port):
        self.socket = None
        self.host = host
        self.port = port
        self.uuid = self.getUUID()
        self.working = False

        self.connect()

    def getUUID(self) -> str:
        return uuid.getnode()

    def connect(self) -> None:
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def close(self) -> None:
        if self.socket:
            self.socket.close()

    def send(self, data) -> None:
        if self.socket:
            try:
                self.socket.sendto(data, (self.host, self.port))
            except Exception as e:
                print(f"Exception while sending: {e}")

    def ping(self) -> None:
        """Report status to CServer in defined intervals"""

        msg_pack = struct.pack(MSG_FMT, self.get_state(), generate_rnd_msg().encode('utf-8'))
        dgram_pack = struct.pack(HEADER_FMT, self.uuid, 0, msg_pack)
        self.send(dgram_pack)

    def listen(self) -> None:
        while True:
            data, a = self.socket.recvfrom(BUFFER_SIZE, socket.SOCK_NONBLOCK)
            id, cmd, msg = struct.unpack(HEADER_FMT, data)
            print(msg.decode('utf-8'))

    def get_state(self) -> int:
        # randomly change state between IDLE and WORKING
        # just for testing purposes
        return random.randint(IDLE, WORKING)
        #return int(self.working)

    def set_state(self, state):
        self.working = state


def signal_handler(signal, frame):
    raise ExitApp

class ExitApp(Exception):
    pass


class Worker(object):

    def __init__(self, remote, interval):
        self.remote = remote
        self.interval = interval
        self.last_tick = time.time()

        self.thread = Thread(target=self.run, daemon=True)
        self.thread.start()

    def run(self):
        pass


class Ping(Worker):

    def __init__(self, remote, interval):
        Worker.__init__(self, remote, interval)

    def run(self):
        while True:
            if time.time() - self.last_tick > self.interval:
                self.remote.ping()
                self.last_tick = time.time()

            time.sleep(self.interval)


class Listener(Worker):

    def __init__(self, remote, interval = 0):
        Worker.__init__(self, remote, interval)

    def run(self):
        while True:
            self.remote.listen()


if __name__ == '__main__':

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    # Arguments parser
    ap = argparse.ArgumentParser()
    ap.add_argument("-H", "--host", action='store', default=HOST, help=f"server host [default: {HOST}]")
    ap.add_argument("-p", "--port", action='store', default=PORT, help=f"server port [default: {PORT}]")
    args = vars(ap.parse_args())

    workers = []
    try:
        remote = Remote(HOST, PORT)

        ping = Ping(remote, PING_INTERVAL)
        listen = Listener(remote)

        workers = [ping, listen]

        for w in workers:
            w.thread.join()

    except ExitApp:
        # cleanup goes here
        pass
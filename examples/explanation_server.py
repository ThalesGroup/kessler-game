
import socket
import struct
import time
from examples.explanation_client import ExplanationClient


class ExplanationServer:
    """
    This sets up a standard UDP server which will receive explanation messages and send
    back notices that it is ready for another message
    """
    def __init__(self):
        self.listen_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.listen_socket.settimeout(0)
        self.send_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.send_socket.settimeout(0)
        self.host = "127.0.0.1"
        self.listen_port = 5092
        self.listen_addr = (self.host, self.listen_port)
        self.listen_socket.bind(self.listen_addr)

        self.send_port = 5093
        self.send_addr = (self.host, self.send_port)
        self.send_socket.bind(self.send_addr)

        self.count = 0
        self.explanation = None

    def run(self):
        """
        Asks server for object. Unpacks it, and returns it.
        :return:
        """

        t_0 = time.perf_counter()
        flushed = False
        while not flushed:
            t_1 = time.perf_counter()
            try:
                data = self.listen_socket.recv(9000)
                self.explanation = data.decode()
                print(self.explanation)
                self.count += 1

            except BlockingIOError:
                if t_1-t_0 > 0.016:
                    flushed = True
                    self.send_socket.sendto("ready".encode(), (self.host, 5090))

if __name__ == '__main__':

    # Create Server
    explanation_server = ExplanationServer()

    # Run Server
    while True:
        explanation_server.run()


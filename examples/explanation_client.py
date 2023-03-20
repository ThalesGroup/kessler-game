
import socket

class ExplanationClient:

    # Initialize the client
    def __init__(self):
        self.listen_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.listen_socket.settimeout(0)
        self.send_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.send_socket.settimeout(0)
        self.host = "127.0.0.1"
        self.listen_port = 5090
        self.listen_addr = (self.host, self.listen_port)
        self.listen_socket.bind(self.listen_addr)

        self.send_port = 5091
        self.send_addr = (self.host, self.send_port)
        self.send_socket.bind(self.send_addr)

        self.count = 0
        self.explanation = None
        self.ready_to_send = True

    def send_explanation(self, packet):
        """
        Expecting an encoded string as an explaination (i.e. "this_is_a_string".decode())
        """
        # first check to see if the server is ready for us to send
        if self.ready_to_send is False:
            self.flush()
        if self.ready_to_send is True:
            self.send_socket.sendto(packet, (self.host, 5092))
            self.ready_to_send = False

    def flush(self):
        try:
            data = self.listen_socket.recv(9000)
            ready_message = data.decode()
            if ready_message == "ready":
                self.ready_to_send = True
        except BlockingIOError:
            # The server is flushed
            pass

if __name__ == '__main__':

    explanation_client = ExplanationClient()
    while True:
        explanation_client.send_explanation("This is a test".encode())

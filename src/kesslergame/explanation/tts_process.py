import pyttsx3
import socket
import time


class Explainer:
    def __init__(self):
        self.engine = pyttsx3.init()
        self._exp_string = None
        self._exp_len = None
        self.msg_server = TTSMessageServer()
        self.should_close = False

    def run_server(self):
        while not self.should_close:
            msg = self.msg_server.get_msg()
            if msg == "!close":
                self.should_close = True
            elif msg is not None:
                self.exp_string = msg

            if self.exp_string is not None:
                self.explain()

        self.msg_server.close()

    @property
    def exp_string(self):
        return self._exp_string

    @exp_string.setter
    def exp_string(self, exp):
        self._exp_string = exp
        self._exp_len = len(exp)

    def clear_exp_string(self):
        self._exp_string = None
        self._exp_len = None

    def explain(self):
        if self._exp_len > 0:
            self.engine.say(self._exp_string)
            self.engine.runAndWait()
            self.clear_exp_string()
        else:
            # warnings.warn("Explanation string has 0 length")
            pass


class TTSMessageServer:
    def __init__(self):
        # Establish communication host and ports
        self.host = '127.0.0.1'
        self.receive_port = 5093
        self.send_port = 5092

        # Instantiate and bind send/receive ports
        self.receive_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.receive_sock.settimeout(0)
        self.receive_sock.bind((self.host, self.receive_port))

        # Instantiate other misc variables needed
        self.receive_count = 0
        self.tts_str = None
        self.ready_to_send = True

    def close(self):
        self.receive_sock.close()

    def get_msg(self) -> str:
        t_0 = time.perf_counter()
        flushed = False
        # Flush through entire buffer to ensure we only read the most recent message
        while not flushed:
            t_1 = time.perf_counter()
            try:
                data = self.receive_sock.recv(9000)
                self.tts_str = data.decode()
                self.receive_count += 1
            except BlockingIOError:
                if t_1 - t_0 > 0.016:
                    flushed = True
        return self.tts_str


def run_tts_process():
    exp = Explainer()
    exp.run_server()

if __name__ == "__main__":
    run_tts_process()

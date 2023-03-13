import pyttsx3
import warnings
from threading import Thread
import time
from multiprocessing import Process, Pipe


# class Explanation:
#     def __init__(self, exp : str = ""):
#         self.inprogress = False
#         self.engine = pyttsx3.init()
#         self.exp_string = exp
#         self.exp_len = len(exp)
#
#         self.engine.connect('started-utterance', self.onStart)
#         # self.engine.connect('started-word', self.onWord)
#         self.engine.connect('finished-utterance', self.onEnd)
#
#     def set_exp(self, exp):
#         self.exp_string = exp
#         self.exp_len = len(exp)
#
#     def get_exp(self):
#         return self.exp_string
#
#     def explain(self):
#         if self.exp_len > 0:
#             print(self.exp_string)
#             self.engine.say(self.exp_string)
#             self.engine.runAndWait()
#         else:
#             warnings.warn("Explanation string has 0 length")
#
#     def give_explanation(self):
#         if not self.inprogress:
#             self.explain()
#
#     def onStart(self, name):
#         # print('starting', name)
#         self.inprogress = True
#
#
#     def onWord(self, name, location, length):
#         # print('word', name, location, length)
#         print(self.inprogress)
#
#
#     def onEnd(self, name, completed):
#         # print('finishing', name, completed)
#         self.inprogress = False


def onStart(self, name):
    print('starting', name)
    # self.inprogress = True


# def onWord(self, name, location, length):
    # print('word', name, location, length)
    # print(self.inprogress)


def onEnd(self, name, completed):
    print('finishing', name, completed)
    return completed
    # self.inprogress = False


def shoutcast_explanation(msg_connection, status_connection):
    # exp_str = "The quick brown fox jumped over the lazy dog"
    run_status = True
    able_to_receive = True
    engine = pyttsx3.init()
    # engine.connect('started-utterance', onStart)
    # engine.connect('started-word', self.onWord)
    # engine.connect('finished-utterance', onEnd)
    while run_status:
        # if able_to_receive:
        exp_str, run_status = msg_connection.recv()
        status_connection.send(False)

        print("Received {}".format(exp_str), flush=True)
        # engine = pyttsx3.init()
        # engine.connect('started-utterance', onStart)
        # # engine.connect('started-word', self.onWord)
        # engine.connect('finished-utterance', onEnd
        engine.say(exp_str)
        engine.runAndWait()
        status_connection.send(True)


def send_message(connection, msg):
    connection.send(msg)


def repeat_explanation():
    num_repeats = 5
    for ii in range(num_repeats):
        shoutcast_explanation()


def main_loop(msg_con, status_con):
    ii = 0
    run_status = True
    first_iter = True

    while run_status:
        ii += 1
        print(ii)

        if not first_iter:
            ready = status_con.recv()
        else:
            first_iter = False
            ready = True

        if ready:
            msg = "  " + str(ii)
            print("Sending msg {}".format(msg), flush=True)
            msg_con.send((msg, run_status))

        time.sleep(0.1)
        if ii >= 150:
            run_status = False


if __name__ == "__main__":
    # explanation_str = "The quick brown fox jumped over the lazy dog"
    # explanation = Explanation(explanation_str)

    msg_conn1, msg_conn2 = Pipe(duplex=True)
    status_conn1, status_conn2 = Pipe(duplex=True)

    p1 = Process(target=shoutcast_explanation, args=(msg_conn1, status_conn1))
    # p1 = Process(target=repeat_explanation)
    p2 = Process(target=main_loop, args=(msg_conn2, status_conn2))
    #
    p1.start()
    p2.start()

    p1.join()
    p2.join()



    # ii = 0
    # for ii in range(500):
    #     if explanation.inprogress:
    #         print(ii)
    #         thread.
    #     # print(explanation.inprogress)
    #     time.sleep(0.1)
    #         # thread.start()
    # thread.join()

    # engine = pyttsx3.init()
    # engine.connect('started-utterance', onStart)
    # # engine.connect('started-word', onWord)
    # engine.connect('finished-utterance', onEnd)
    # engine.say('  20')
    # engine.runAndWait()
    # engine.say("  40")
    # engine.runAndWait()

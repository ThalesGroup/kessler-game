
import pyttsx3
from examples.explanation_server import ExplanationServer

class Explanation:
    def __init__(self):
        self.engine = pyttsx3.init()
        self.exp_string = None
        self.exp_len = None
        self.exp_server = ExplanationServer()

    def run_server(self):
        self.exp_server.run()
        if self.exp_server.explanation is not None:
            self.set_exp(self.exp_server.explanation)

    def set_exp(self, exp):
        self.exp_string = exp
        self.exp_len = len(exp)

    def get_exp(self):
        return self.exp_string

    def explain(self):
        if self.exp_len > 0:
            self.engine.say(self.exp_string)
            self.engine.runAndWait()
        else:
            # warnings.warn("Explanation string hself.engine.say(as 0 length")
            pass

if __name__ == "__main__":
    exp = Explanation()
    while True:
        exp.run_server()
        if exp.exp_string is not None:
            exp.explain()

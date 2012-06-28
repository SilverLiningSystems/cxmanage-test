import sys
import threading
import time

class Indicator(threading.Thread):
    """ An indicator that prints a message with trailing dots, I.E.

    Updating... """

    def __init__(self, message):
        threading.Thread.__init__(self)
        self.lock = threading.Lock()
        self.message = message
        self.running = False

    def run(self):
        self.lock.acquire()

        sys.stdout.write(self.message)
        sys.stdout.flush()

        self.running = True
        while self.running:
            sys.stdout.write(".")
            sys.stdout.flush()
            self.lock.release()
            time.sleep(1)
            self.lock.acquire()

        self.lock.release()

    def stop(self):
        self.lock.acquire()

        if self.running:
            sys.stdout.write("\n")
            sys.stdout.flush()
            self.running = False

        self.lock.release()

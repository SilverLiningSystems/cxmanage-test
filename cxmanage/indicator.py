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
        counter = 0
        while self.running:
            if counter == 0:
                sys.stdout.write(".")
                sys.stdout.flush()

            self.lock.release()
            time.sleep(0.1)
            self.lock.acquire()

            counter = (counter + 1) % 10

        self.lock.release()

    def stop(self):
        self.lock.acquire()

        if self.running:
            sys.stdout.write("\n")
            sys.stdout.flush()
            self.running = False

        self.lock.release()

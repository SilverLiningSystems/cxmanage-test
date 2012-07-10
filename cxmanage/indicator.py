# Copyright (c) 2012, Calxeda Inc.
#
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
# * Redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer.
# * Redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution.
# * Neither the name of Calxeda Inc. nor the names of its contributors
# may be used to endorse or promote products derived from this software
# without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT HOLDERS OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS
# OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR
# TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF
# THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH
# DAMAGE.

import sys
import threading
import time

class Indicator(threading.Thread):
    """ An indicator that prints a message with trailing dots, I.E.

    Updating... """

    def __init__(self, total):
        threading.Thread.__init__(self)
        self.lock = threading.Lock()
        self.daemon = True
        self.running = False

        self.total = total
        self.successes = 0
        self.errors = 0

    def run(self):
        self.lock.acquire()

        message = "\r%i successes  |  %i errors  |  %i nodes left  |  %s"

        # Print initial message
        nodes_left = self.total - self.successes - self.errors
        dots = ""
        sys.stdout.write(message % (self.successes,
                self.errors, nodes_left, dots.ljust(3)))
        sys.stdout.flush()

        self.running = True
        while self.running:
            self.lock.release()
            time.sleep(0.25)
            self.lock.acquire()

            nodes_left = self.total - self.successes - self.errors
            if len(dots) >= 3:
                dots = ""
            else:
                dots += "."

            sys.stdout.write(message % (self.successes,
                self.errors, nodes_left, dots.ljust(3)))
            sys.stdout.flush()

        self.lock.release()

    def stop(self):
        self.lock.acquire()
        was_running = self.running
        self.running = False
        self.lock.release()

        if was_running:
            self.join()

    def add_success(self):
        self.lock.acquire()
        self.successes += 1
        self.lock.release()

    def add_error(self):
        self.lock.acquire()
        self.errors += 1
        self.lock.release()

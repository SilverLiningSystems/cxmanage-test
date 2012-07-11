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
    """ An indicator that prints a message indicating the current command
    status. """

    def __init__(self, targets, results, errors):
        threading.Thread.__init__(self)
        self.lock = threading.Lock()
        self.daemon = True
        self.running = False

        self.total = len(targets)
        self.results = results
        self.errors = errors

        self.counter = 0

    def run(self):
        """ Continously print message until a stop signal is received """
        self.lock.acquire()

        # Print initial message
        self._print_message()

        self.running = True
        while self.running:
            self.lock.release()
            time.sleep(0.25)
            self.lock.acquire()

            self._print_message()

        self.lock.release()

    def stop(self):
        """ Stop the indicator """
        self.lock.acquire()
        was_running = self.running
        self.running = False
        self.lock.release()

        if was_running:
            self.join()

    def _print_message(self):
        """ Print a single message """
        message = "\r%i successes  |  %i errors  |  %i nodes left  |  %s"
        successes = len(self.results)
        errors = len(self.errors)
        nodes_left = self.total - successes - errors
        dots = "".join(["." for x in range(self.counter % 4)]).ljust(3)
        self.counter += 1

        sys.stdout.write(message % (successes, errors, nodes_left, dots))
        sys.stdout.flush()

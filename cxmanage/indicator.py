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
        deadline = time.time()
        while self.running:
            current_time = time.time()
            if current_time >= deadline:
                deadline = current_time + 1
                sys.stdout.write(".")
                sys.stdout.flush()

            self.lock.release()
            time.sleep(0.1)
            self.lock.acquire()

        self.lock.release()

    def stop(self):
        self.lock.acquire()

        if self.running:
            sys.stdout.write("\n")
            sys.stdout.flush()
            self.running = False

        self.lock.release()

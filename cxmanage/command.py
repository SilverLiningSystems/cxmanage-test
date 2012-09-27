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

from time import sleep
from threading import Thread, Lock

class Command:
    """ A command object that runs a given method across multiple targets.

    It's designed to have an interface similar to that of a thread, with
    methods such as start(), join(), is_alive(), etc.

    The command object is not itself a thread, but it does contain multiple
    worker threads. The function is executed in parallel across all of the
    targets, so make sure the targets don't depend on eachother in any way. """


    ############################ Public methods ###############################

    def __init__(self, targets, name, args, delay=0, num_threads=1):
        self.results = {}
        self.errors = {}

        self._lock = Lock()
        self._targets = targets[:]
        self._name = name
        self._args = args
        self._delay = delay
        self._workers = [CommandWorker(self) for i in range(num_threads)]

    def start(self):
        """ Start the command """
        for worker in self._workers:
            worker.start()

    def join(self):
        """ Wait for the command to finish """
        for worker in self._workers:
            worker.join()

    def is_alive(self):
        """ Return true if the command is still running """
        return any([x.is_alive() for x in self._workers])


    ################## Private methods for CommandWorkers #####################

    def _get_next_target(self):
        """ Get the next target to operate on. """
        self._lock.acquire()

        # TODO: make this more efficient. We probably don't want to be slicing
        # the array every single time.
        if self._targets:
            target = self._targets[0]
            self._targets = self._targets[1:]
        else:
            target = None

        self._lock.release()
        return target

    def _set_result(self, address, result):
        """ Set the result for a given address """
        self._lock.acquire()
        self.results[address] = result
        self._lock.release()

    def _set_error(self, address, error):
        """ Set an error for the given address """
        self._lock.acquire()
        self.errors[address] = error
        self._lock.release()


class CommandWorker(Thread):
    """ A worker thread for a command.

    Once started, the worker will obtain targets from the pool and run the
    named method on them. The thread terminates once there are no targets
    remaining in the pool. """

    def __init__(self, command):
        Thread.__init__(self)
        self.daemon = True
        self.command = command

    def run(self):
        """ Run the named method on some targets, then terminate """

        target = self.command._get_next_target()
        while target != None:
            try:
                sleep(self.command._delay)
                method = getattr(target, self.command._name)
                result = method(*self.command._args)
                self.command._set_result(target.address, result)
            except Exception as e:
                self.command._set_error(target.address, e)
            target = self.command._get_next_target()

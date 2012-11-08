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


class CommandFailedError(Exception):
    """ Error that indicates a command has failed """
    def __init__(self, results, errors):
        self.results = results
        self.errors = errors


class CommandStatus:
    """ Container for command status """
    def __init__(self, successes, errors, nodes_left):
        self.successes = successes
        self.errors = errors
        self.nodes_left = nodes_left


class Command:
    """ A command object that runs a given method across multiple nodes.

    It's designed to have an interface similar to that of a thread, with
    methods such as start(), join(), is_alive(), etc.

    The command object is not itself a thread, but it does contain multiple
    worker threads. The function is executed in parallel across all of the
    nodes, so make sure the nodes don't depend on eachother in any way. """


    ############################ Public methods ###############################

    def __init__(self, nodes, name, args, delay=0, max_threads=1):
        self._lock = Lock()

        self._node_iterator = iter(nodes)
        self._node_count = len(nodes)

        self._name = name
        self._args = args
        self._delay = delay

        num_threads = min(max_threads, self._node_count)
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

    def get_results(self):
        """ Get the results of this command.

        Returns a { ip_address : result } dictionary of results.

        Raises a CommandFailedError if there were any errors. """
        results = {}
        errors = {}
        for worker in self._workers:
            results.update(worker.results)
            errors.update(worker.errors)

        if errors:
            raise CommandFailedError(results, errors)
        return results

    def get_status(self):
        """ Get the status of this command.

        Returns a CommandStatus object. """
        successes = 0
        errors = 0
        for worker in self._workers:
            successes += len(worker.results)
            errors += len(worker.errors)
        nodes_left = self._node_count - successes - errors
        return CommandStatus(successes, errors, nodes_left)

    ################## Private methods for CommandWorkers #####################

    def _get_next_node(self):
        """ Get the next node to operate on. """
        self._lock.acquire()
        try:
            return self._node_iterator.next()
        finally:
            self._lock.release()


class CommandWorker(Thread):
    """ A worker thread for a command.

    Once started, the worker will obtain nodes from the pool and run the
    named method on them. The thread terminates once there are no nodes
    remaining. """

    def __init__(self, command):
        Thread.__init__(self)
        self.daemon = True
        self.command = command
        self.results = {}
        self.errors = {}

    def run(self):
        """ Run the named method on some nodes, store the results/errors, then
        terminate. """
        try:
            while True:
                node = self.command._get_next_node()
                try:
                    sleep(self.command._delay)
                    method = getattr(node, self.command._name)
                    result = method(*self.command._args)
                    self.results[node] = result
                except Exception as e:
                    self.errors[node] = e
        except StopIteration:
            pass

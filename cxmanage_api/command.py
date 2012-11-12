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
"""Cxmanage Python API: Command, CommandWorker

:requires: time
:requires: threading
:requires: cxmanage_api.cx_exceptions

"""

from time import sleep
from threading import Thread, Lock
from cxmanage_api.cx_exceptions import CommandFailedError


class CommandWorker(Thread):
    """A worker thread for a command.

    A worker will obtain nodes from the pool and run the named method on them
    once started (i.e. start() is called). 
    The thread terminates once there are no nodes remaining.
    """

    def __init__(self, command):
        """Default constructor for the CommandWorker class.
        
        :param command: The command to run.
        :type command: Command
        """
        Thread.__init__(self)
        self.daemon = True
        self.command = command
        self.results = {}
        self.errors = {}

    def run(self):
        """Runs the named method, stores results/errors, then terminates."""
        try:
            while (True):
                node = self.command._get_next_node()
                try:
                    sleep(self.command._delay)
                    method = getattr(node, self.command._name)
                    result = method(*self.command._args)
                    self.results[str(node)] = result
                
                except Exception as e:
                    self.errors[node] = e
        
        except StopIteration:
            pass
        
        
class Command:
    """Command objects are containers/managers of multi-threaded CommandWorkers
    that execute commands in parallel on a node(s) & fabric(s).
    
    .. note::
        * They are designed to have an interface similar to that of a thread.
          but are not threads themselves. The CommandWorkers are the threads.
        * start(), run(), join(), is_alive()
    
    :param nodes: Nodes to execute commands on.
    :type nodes: Node
    :param name: Named command to run.
    :type name: string
    :param args: Arguments to pass on to the command.
    :type args: list
    :param delay: Time to wait before issuing the next command. Default=0
    :type delay: integer
    :param max_threads: Maximum number of threads to spawn at a time.
    :type max_threads: integer
    """

    def __init__(self, nodes, name, args, delay=0, max_threads=1):
        """Default constructor for the Command class.
        
        :param nodes: Nodes to execute commands on.
        :type nodes: Node
        :param name: Named command to run.
        :type name: string
        :param args: Arguments to pass on to the command.
        :type args: list
        :param delay: Time to wait before issuing the next command. Default=0
        :type delay: integer
        :param max_threads: Maximum number of threads to spawn at a time.
        :type max_threads: integer
        """
        self._lock = Lock()
        self._node_iterator = iter(nodes)
        self._node_count = len(nodes)
        self._name = name
        self._args = args
        self._delay = delay
        num_threads = min(max_threads, self._node_count)
        self._workers = [CommandWorker(self) for i in range(num_threads)]

    def start(self):
        """Starts the command."""
        for worker in self._workers:
            worker.start()

    def join(self):
        """Waits for the command to finish."""
        for worker in self._workers:
            worker.join()

    def is_alive(self):
        """Tests to see if the command is alive.
        
        :return: Whether or not the command is alive.
        :rtype: boolean
        """
        return any([x.is_alive() for x in self._workers])

    def get_results(self):
        """Gets the command results.
        
        :raises: CommandFailedError
        
        :return: Results of this commands.
        :rtype: dictionary
        """
        results, errors = {}, {}
        for worker in self._workers:
            results.update(worker.results)
            errors.update(worker.errors)
        if (errors):
            raise CommandFailedError(results, errors)
        return results

    def get_status(self):
        """ Get the status of this command.

        :return: The commands status.
        :rtype: CommandStatus
        """
        class CommandStatus:
            """Container for a commands status."""
    
            def __init__(self, successes, errors, nodes_left):
                """Default constructor for the CommandStatus class.
                
                :param successes: The successes/ip node map for this command.
                :type successes: dictionary
                :param errors: The errors/ip node map for this command.
                :type errors: dictionary
                :param nodes_left: The number of nodes left to execute the command.
                :type nodes_left: integer
                """
                self.successes = successes
                self.errors = errors
                self.nodes_left = nodes_left
        
        #       
        # get_status()
        #        
        successes, errors = 0
        for worker in self._workers:
            successes += len(worker.results)
            errors += len(worker.errors)
        nodes_left = self._node_count - successes - errors
        return CommandStatus(successes, errors, nodes_left)

    def _get_next_node(self):
        """Gets the next node to operate on."""
        self._lock.acquire()
        try:
            return self._node_iterator.next()
        finally:
            self._lock.release()


# End of file: ./command.py

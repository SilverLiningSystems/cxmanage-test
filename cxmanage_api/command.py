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
from cxmanage_api.cx_exceptions import CommandFailedError


class CommandWorker(Thread):
    """A worker thread for a `Command <command.html>`_.

    A CommandWorker will obtain nodes from the pool and run the named method on
    them once started. The thread terminates once there are no nodes remaining.

    >>> from cxmanage_api.command import CommandWorker
    >>> cw = CommandWorker(command=cmd)

    :param command: The command to run.
    :type command: Command

    """

    def __init__(self, command):
        """Default constructor for the CommandWorker class."""
        super(CommandWorker, self).__init__()
        self.daemon = True
        self.command = command
        self.results = {}
        self.errors = {}

    def run(self):
        """Runs the named method, stores results/errors, then terminates.

        >>> cw.run()

        """
        try:
            while (True):
                key, node = self.command._get_next_node()
                try:
                    sleep(self.command._delay)
                    method = getattr(node, self.command._name)
                    result = method(*self.command._args)
                    self.results[key] = result
                except Exception as e:
                    self.errors[key] = e
        except StopIteration:
            pass


class Command:
    """Commands are containers/managers of multi-threaded CommandWorkers.

    .. note::
        * Commands are designed to have an interface similar to a thread,
          but they are not threads. The CommandWorkers are the actual threads.

    >>> # Create a list of Nodes ...
    >>> from cxmanage_api.node import Node
    >>> n1 = Node('10.20.1.9')
    >>> n2 = Node('10.20.2.131')
    >>> nodes = [n1, n2]
    >>> #
    >>> # Typical instantiation ...
    >>> # (this example gets the mac addresses which takes no arguments)
    >>> #
    >>> from cxmanage_api.command import Command
    >>> cmd = Command(nodes=nodes, name='get_mac_addresses', args=[])

    :param nodes: Nodes to execute commands on.
    :type nodes: list
    :param name: Named command to run.
    :type name: string
    :param args: Arguments to pass on to the command.
    :type args: list
    :param delay: Time to wait before issuing the next command.
    :type delay: integer
    :param max_threads: Maximum number of threads to spawn at a time.
    :type max_threads: integer

    """

    def __init__(self, nodes, name, args, delay=0, max_threads=1):
        """Default constructor for the Command class."""
        self._lock = Lock()

        try:
            self._node_iterator = nodes.iteritems()
        except AttributeError:
            self._node_iterator = iter([(x, x) for x in nodes])
        self._node_count = len(nodes)

        self._name = name
        self._args = args
        self._delay = delay

        num_threads = min(max_threads, self._node_count)
        self._workers = [CommandWorker(self) for i in range(num_threads)]

    def start(self):
        """Starts the command.

        >>> cmd.start()

        """
        for worker in self._workers:
            worker.start()

    def join(self):
        """Waits for the command to finish.

        >>> cmd.join()

        """
        for worker in self._workers:
            worker.join()

    def is_alive(self):
        """Tests to see if the command is alive.

        >>> # Command is still in progress ... (i.e. has nodes still running it)
        >>> cmd.is_alive()
        True
        >>> # Command has completed. (or failed)
        >>> cmd.is_alive()
        False

        :return: Whether or not the command is alive.
        :rtype: boolean

        """
        return any([x.is_alive() for x in self._workers])

    def get_results(self):
        """Gets the command results.

        >>> cmd.get_results()
        {<cxmanage_api.node.Node object at 0x7f8a99940cd0>:
            ['fc:2f:40:3b:ec:40', 'fc:2f:40:3b:ec:41', 'fc:2f:40:3b:ec:42'],
         <cxmanage_api.node.Node object at 0x7f8a99237a90>:
            ['fc:2f:40:91:dc:40', 'fc:2f:40:91:dc:41', 'fc:2f:40:91:dc:42']}

        :return: Results of this commands.
        :rtype: dictionary

        :raises CommandFailedError: If The command results contains ANY errors.

        """
        results, errors = {}, {}
        for worker in self._workers:
            results.update(worker.results)
            errors.update(worker.errors)
        if (errors):
            raise CommandFailedError(results, errors)
        return results

    def get_status(self):
        """Gets the status of this command.

        >>> status = cmd.get_status()
        >>> status.successes
        2
        >>> status.errors
        0
        >>> status.nodes_left
        0

        :return: The commands status.
        :rtype: CommandStatus

        """


        class CommandStatus:
            """Container for a commands status."""

            def __init__(self, successes, errors, nodes_left):
                """Default constructor for the CommandStatus class."""
                self.successes = successes
                self.errors = errors
                self.nodes_left = nodes_left

        #
        # get_status()
        #
        successes = 0
        errors = 0
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

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

from Queue import Queue
from threading import Thread
from time import sleep

class Task(object):
    """ A task object representing some unit of work to be done. """
    def __init__(self, method, *args):
        self._method = method
        self._args = args

        self.status = "Queued"

    def join(self):
        """ Wait for this task to finish """
        while self.is_alive():
            pass # TODO: don't busy wait here

    def is_alive(self):
        """ Return true if this task hasn't been finished """
        return not self.status in ["Completed", "Failed"]

class TaskQueue(object):
    """ A task queue, consisting of a queue and a number of workers. """

    def __init__(self, threads=48, delay=0):
        self._queue = Queue()
        self._workers = [TaskWorker(task_queue=self, delay=delay)
                for x in xrange(threads)]

    def put(self, method, *args):
        """
        Add a task to the task queue.

        method: a method to call
        args: args to pass to the method

        returns: a Task object that will be executed by a worker at a later
        time.
        """
        task = Task(method, *args)
        self._queue.put(task)
        return task

    def get(self):
        """
        Get a task from the task queue. Mainly used by workers.

        returns: a Task object that hasn't been executed yet.
        """
        return self._queue.get()

class TaskWorker(Thread):
    """ A TaskWorker that executes tasks from a TaskQueue. """
    def __init__(self, task_queue, delay=0):
        super(TaskWorker, self).__init__()
        self.daemon = True

        self._task_queue = task_queue
        self._delay = delay

        self.start()

    def run(self):
        """ Repeatedly get tasks from the TaskQueue and execute them. """
        while True:
            sleep(self._delay)
            task = self._task_queue.get()
            task.status = "In Progress"
            try:
                task.result = task._method(*task._args)
                task.status = "Completed"
            except Exception as e:
                task.error = e
                task.status = "Failed"

DEFAULT_TASK_QUEUE = TaskQueue()

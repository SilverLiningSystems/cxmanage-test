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

import unittest
import random
import time

from cxmanage.command import Command, CommandWorker

NUM_NODES = 128
ADDRESSES = ["192.168.100.%i" % x for x in range(1, NUM_NODES+1)]

class CommandTest(unittest.TestCase):
    def setUp(self):
        addresses = ADDRESSES[:]
        random.shuffle(addresses)

        self.good_targets = [DummyTarget(x) for x in addresses[:NUM_NODES/2]]
        self.bad_targets = [DummyTarget(x, True)
                for x in addresses[NUM_NODES/2:]]
        self.targets = self.good_targets + self.bad_targets

    def test_worker(self):
        """ Test the command worker thread """
        command = DummyCommand(self.targets)
        worker = CommandWorker(command)
        worker.start()
        worker.join()

        self.assertEqual(len(command.results), len(self.good_targets))
        self.assertEqual(len(command.errors), len(self.bad_targets))

        for target in self.good_targets:
            self.assertEqual(target.executed, [("action", ("a", "b", "c"))])
            self.assertTrue((target.address, "action_result")
                    in command.results)
        for target in self.bad_targets:
            self.assertEqual(target.executed, [("action", ("a", "b", "c"))])
            self.assertTrue((target.address, "action_error")
                    in command.errors)

    def test_command(self):
        """ Test the command spawner """
        command = Command(self.targets, "action", ("a", "b", "c"),
                max_threads=32)
        command.start()
        command.join()

        for target in self.good_targets:
            self.assertEqual(target.executed, [("action", ("a", "b", "c"))])
            self.assertEqual(command.results[target.address], "action_result")
        for target in self.bad_targets:
            self.assertEqual(target.executed, [("action", ("a", "b", "c"))])
            self.assertEqual(str(command.errors[target.address]),
                    "action_error")

    def test_command_delay(self):
        """ Test the command delay argument """
        delay = 1
        expected_duration = 4
        max_threads = NUM_NODES / expected_duration

        command = Command(self.targets, "action", ("a", "b", "c"),
                delay=delay, max_threads=max_threads)

        start_time = time.time()
        command.start()
        command.join()
        end_time = time.time()

        self.assertGreaterEqual(end_time - start_time, expected_duration)

class DummyTarget:
    def __init__(self, address, fail=False):
        self.address = address
        self.fail = fail
        self.executed = []

    def action(self, *args):
        self.executed.append(("action", args))
        if self.fail:
            raise ValueError("action_error")
        return "action_result"

class DummyCommand:
    def __init__(self, targets):
        self.results = []
        self.errors = []

        self._targets = targets
        self._name = "action"
        self._args = ("a", "b", "c")
        self._delay = 0

    def _get_next_target(self):
        if not self._targets:
            return None
        target = self._targets[0]
        self._targets = self._targets[1:]
        return target

    def _set_result(self, address, result):
        self.results.append((address, result))

    def _set_error(self, address, error):
        self.errors.append((address, str(error)))

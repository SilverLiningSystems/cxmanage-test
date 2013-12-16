# pylint: disable=too-many-public-methods

# Copyright (c) 2012-2013, Calxeda Inc.
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

""" Tests for the cxmanage_api.credentials module """

import unittest

from cxmanage_api.credentials import Credentials


class TestCredentials(unittest.TestCase):
    """ Unit tests for the Credentials class """
    def test_default(self):
        """ Test default Credentials object """
        creds = Credentials()
        self.assertEqual(vars(creds), Credentials.defaults)

    def test_from_dict(self):
        """ Test Credentials instantiated with a dict """
        creds = Credentials({"linux_password": "foo"})
        expected = dict(Credentials.defaults)
        expected["linux_password"] = "foo"
        self.assertEqual(vars(creds), expected)

    def test_from_kwargs(self):
        """ Test Credentials instantiated with kwargs """
        creds = Credentials(linux_password="foo")
        expected = dict(Credentials.defaults)
        expected["linux_password"] = "foo"
        self.assertEqual(vars(creds), expected)

    def test_from_credentials(self):
        """ Test Credentials instantiated with other Credentials """
        creds = Credentials(Credentials(linux_password="foo"))
        expected = dict(Credentials.defaults)
        expected["linux_password"] = "foo"
        self.assertEqual(vars(creds), expected)

    def test_fails_on_invalid(self):
        """ Test that we don't allow unrecognized credentials """
        with self.assertRaises(ValueError):
            Credentials({"desire_to_keep_going": "Very Low"})
        with self.assertRaises(ValueError):
            Credentials(magical_mystery_cure="Writing silly strings!")

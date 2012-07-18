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


import os
import shutil
import tempfile
import unittest

from cxmanage.tftp import InternalTftp, ExternalTftp

from cxmanage_test import random_file

class InternalTftpTest(unittest.TestCase):
    """ Tests involving an internal TFTP server """

    def setUp(self):
        self.work_dir = tempfile.mkdtemp(prefix="cxmanage_test-")
        self.tftp = InternalTftp()

    def tearDown(self):
        shutil.rmtree(self.work_dir)

    def test_put_and_get(self):
        """ Test file transfers on an internal host """

        # Create file
        filename = random_file(self.work_dir, 1024)
        contents = open(filename).read()

        # Upload and remove
        basename = os.path.basename(filename)
        self.tftp.put_file(filename, basename)
        os.remove(filename)
        self.assertFalse(os.path.exists(filename))

        # Download
        self.tftp.get_file(basename, filename)

        # Verify match
        self.assertEqual(open(filename).read(), contents)

class ExternalTftpTest(unittest.TestCase):
    """ Tests involving an external TFTP server.

    For testing purposes the 'external' server points to an internally hosted
    one, but it allows us to make sure the actual TFTP protocol is working. """

    def setUp(self):
        self.work_dir = tempfile.mkdtemp(prefix="cxmanage_test-")

        # Set up an internal server
        self.internal_tftp = InternalTftp()

        # Set up external server
        address = "localhost"
        port = self.internal_tftp.get_port()
        self.tftp = ExternalTftp(address, port)

    def tearDown(self):
        shutil.rmtree(self.work_dir)

    def test_put_and_get(self):
        """ Test file transfers on an external host """

        # Create file
        filename = random_file(self.work_dir, 1024)
        contents = open(filename).read()

        # Upload and remove original file
        basename = os.path.basename(filename)
        self.tftp.put_file(filename, basename)
        os.remove(filename)
        self.assertFalse(os.path.exists(filename))

        # Download
        self.tftp.get_file(basename, filename)

        # Verify match
        self.assertEqual(open(filename).read(), contents)

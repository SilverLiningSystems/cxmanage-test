import logging
import os
import random
import shutil
import tempfile
import unittest

from tftpy import setLogLevel

from cxmanage.tftp import Tftp

class InternalTftpTest(unittest.TestCase):
    """ Tests involving an internal TFTP server """

    def setUp(self):
        self.work_dir = tempfile.mkdtemp()

        self.tftp = Tftp()
        self.tftp.set_internal_server(self.work_dir)
        setLogLevel(logging.ERROR)

    def tearDown(self):
        self.tftp.kill_server()
        shutil.rmtree(self.work_dir)

    def test_put_and_get(self):
        """ Test file transfers on an internal host """

        # Create file
        contents = "".join([chr(random.randint(0, 255)) for a in range(1024)])
        filename = tempfile.mkstemp(prefix="%s/" % self.work_dir)[1]
        open(filename, "w").write(contents)

        # Upload
        basename = os.path.basename(filename)
        self.tftp.put_file(filename, basename)

        # Download
        self.tftp.get_file(basename, filename)

        # Verify match
        self.assertEqual(open(filename).read(), contents)

class ExternalTftpTest(unittest.TestCase):
    """ Tests involving an external TFTP server.

    For testing purposes the 'external' server points to an internally hosted
    one, but it allows us to make sure the actual TFTP protocol is working. """

    def setUp(self):
        self.work_dir = tempfile.mkdtemp()
        self.tftp_dir = tempfile.mkdtemp()

        # Set up an internal server
        self.internal_tftp = Tftp()
        self.internal_tftp.set_internal_server(self.tftp_dir)

        # Get address and port
        address = "localhost"
        port = self.internal_tftp.get_port()

        # Set up an external server
        self.tftp = Tftp()
        self.tftp.set_external_server(address, port)
        setLogLevel(logging.ERROR)

    def tearDown(self):
        self.internal_tftp.kill_server()
        shutil.rmtree(self.tftp_dir)
        shutil.rmtree(self.work_dir)

    def test_put_and_get(self):
        """ Test file transfers on an external host """

        # Create file
        contents = "".join([chr(random.randint(0, 255)) for a in range(1024)])
        filename = tempfile.mkstemp(prefix="%s/" % self.work_dir)[1]
        open(filename, "w").write(contents)

        # Upload and remove original file
        basename = os.path.basename(filename)
        self.tftp.put_file(filename, basename)
        os.remove(filename)
        self.assertFalse(os.path.exists(filename))

        # Download
        self.tftp.get_file(basename, filename)

        # Verify match
        self.assertEqual(open(filename).read(), contents)

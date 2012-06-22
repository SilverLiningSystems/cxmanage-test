import os
import random
import shutil
import string
import tempfile
import time
import unittest

from cxmanage.tftp import Tftp

class InternalTftpTest(unittest.TestCase):
    def setUp(self):
        self.work_dir = tempfile.mkdtemp()

        self.tftp = Tftp()
        self.tftp.set_internal_server(self.work_dir)

    def tearDown(self):
        self.tftp.kill_server()
        shutil.rmtree(self.work_dir)

    def test_put_and_get(self):
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

    def tearDown(self):
        self.internal_tftp.kill_server()
        shutil.rmtree(self.tftp_dir)
        shutil.rmtree(self.work_dir)

    def test_put(self):
        # Create file
        contents = "".join([chr(random.randint(0, 255)) for a in range(1024)])
        filename = tempfile.mkstemp(prefix="%s/" % self.work_dir)[1]
        open(filename, "w").write(contents)

        # Upload
        basename = os.path.basename(filename)
        self.tftp.put_file(filename, basename)

        # Verify match
        self.assertEqual(contents,
                open("%s/%s" % (self.tftp_dir, basename)).read())

    def test_get(self):
        # Create file
        contents = "".join([chr(random.randint(0, 255)) for a in range(1024)])
        filename = tempfile.mkstemp(prefix="%s/" % self.tftp_dir)[1]
        open(filename, "w").write(contents)

        # Download
        basename = os.path.basename(filename)
        self.tftp.get_file(basename, "%s/%s" % (self.work_dir, basename))

        # Verify match
        self.assertEqual(contents,
                open("%s/%s" % (self.work_dir, basename)).read())

    def test_put_and_get(self):
        # Create file
        contents = "".join([chr(random.randint(0, 255)) for a in range(1024)])
        filename = tempfile.mkstemp(prefix="%s/" % self.work_dir)[1]
        open(filename, "w").write(contents)

        # Upload and remove original file
        basename = os.path.basename(filename)
        self.tftp.put_file(filename, basename)
        os.remove(filename)

        # Download
        self.tftp.get_file(basename, filename)

        # Verify match
        self.assertEqual(open(filename).read(), contents)

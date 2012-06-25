import os
import random
import shutil
import struct
import tempfile
import unittest

from cxmanage.simg import has_simg
from cxmanage.image import Image
from cxmanage.tftp import Tftp

# TODO: move this to a better place
class Slot:
    def __init__(self, slot="00", offset="00000000", size="00000000",
            version="00000000", daddr="00000000", in_use="Unknown"):
        self.slot = slot
        self.offset = offset
        self.size = size
        self.version = version
        self.daddr = daddr
        self.in_use = in_use

class ImageTest(unittest.TestCase):
    """ Tests involving cxmanage images

    These will rely on an internally hosted TFTP server. """

    def setUp(self):
        self.work_dir = tempfile.mkdtemp()
        self.tftp_dir = tempfile.mkdtemp()

        # Set up an internal server
        self.tftp = Tftp()
        self.tftp.set_internal_server(self.tftp_dir)

    def tearDown(self):
        self.tftp.kill_server()
        shutil.rmtree(self.tftp_dir)
        shutil.rmtree(self.work_dir)

    def test_upload(self):
        """ Test image creation and upload """
        imglen = 1024
        daddr = 12345
        new_version = 1

        # Create image
        contents = "".join([chr(random.randint(0, 255))
                for a in range(imglen)])
        filename = tempfile.mkstemp(prefix="%s/" % self.work_dir)[1]
        open(filename, "w").write(contents)
        image = Image(filename, "DUMMY")

        # Create slot
        slot = Slot(size = "%8x" % (imglen + 28), daddr = "%8x" % daddr)

        # Upload image
        image_filename = image.upload(self.work_dir, self.tftp, slot, new_version)

        # Examine uploaded image
        simg = open("%s/%s" % (self.tftp_dir, image_filename)).read()
        self.assertTrue(has_simg(simg))
        self.assertEqual(simg[28:], contents)

        # Examine uploaded simg header
        # TODO: replace this when we refactor SIMG
        tup = struct.unpack('<4sHHIIIII', simg[:28])
        self.assertEqual(tup[2], new_version)
        self.assertEqual(tup[4], imglen)
        self.assertEqual(tup[5], daddr)

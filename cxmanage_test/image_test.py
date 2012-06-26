import os
import random
import shutil
import tempfile
import unittest

from cxmanage.simg import get_simg_header
from cxmanage.image import Image
from cxmanage.tftp import InternalTftp

from cxmanage_test import TestFWInfoResult

class ImageTest(unittest.TestCase):
    """ Tests involving cxmanage images

    These will rely on an internally hosted TFTP server. """

    def setUp(self):
        self.work_dir = tempfile.mkdtemp()

        # Set up an internal server
        self.tftp = InternalTftp()

    def tearDown(self):
        shutil.rmtree(self.work_dir)
        self.tftp.kill()

    def test_upload(self):
        """ Test image creation and upload """

        imglen = 1024
        daddr = 12345
        new_version = 1

        # Create image
        random.seed(0) # use a known random seed that won't have a weird type
        contents = "".join([chr(random.randint(0, 255))
                for a in range(imglen)])
        filename = tempfile.mkstemp(prefix="%s/" % self.work_dir)[1]
        open(filename, "w").write(contents)
        image = Image(filename, "RAW")

        # Create slot
        slot = TestFWInfoResult(size=imglen + 28, daddr=daddr)

        # Upload image and delete file
        image_filename = image.upload(self.work_dir,
                self.tftp, slot, new_version)
        os.remove(filename)

        # Download image
        filename = "%s/%s" % (self.work_dir, image_filename)
        self.tftp.get_file(image_filename, filename)

        # Examine image
        simg = open(filename).read()
        header = get_simg_header(simg)
        self.assertEqual(header.version, new_version)
        self.assertEqual(header.imglen, imglen)
        self.assertEqual(header.daddr, daddr)
        self.assertEqual(simg[header.imgoff:], contents)

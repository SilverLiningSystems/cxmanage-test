import random
import shutil
import tempfile
import unittest

from cxmanage.simg import get_simg_header
from cxmanage.image import Image
from cxmanage.tftp import Tftp

from cxmanage_test import TestFWInfoResult

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
        image = Image(filename, "RAW")

        # Create slot
        slot = TestFWInfoResult(size=imglen + 28, daddr=daddr)

        # Upload image
        image_filename = image.upload(self.work_dir, self.tftp, slot, new_version)

        # Examine uploaded image
        simg = open("%s/%s" % (self.tftp_dir, image_filename)).read()
        header = get_simg_header(simg)
        self.assertEqual(header.version, new_version)
        self.assertEqual(header.imglen, imglen)
        self.assertEqual(header.daddr, daddr)
        self.assertEqual(simg[header.imgoff:], contents)

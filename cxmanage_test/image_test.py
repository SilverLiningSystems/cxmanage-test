#Copyright 2012 Calxeda, Inc.  All Rights Reserved.

import os
import shutil
import tempfile
import unittest

from cxmanage.simg import get_simg_header
from cxmanage.image import Image
from cxmanage.tftp import InternalTftp

from cxmanage_test import TestSlot, random_file

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

        class TestImage(Image):
            def valid_type(self):
                return True

        imglen = 1024
        daddr = 12345
        new_version = 1

        # Create image
        filename = random_file(self.work_dir, imglen)
        contents = open(filename).read()
        image = TestImage(filename, "RAW")

        # Create slot
        slot = TestSlot(size=imglen + 28, daddr=daddr)

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

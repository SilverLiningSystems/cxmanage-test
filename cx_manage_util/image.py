#!/bin/env python

import os
import tempfile

from cx_manage_util.simg import create_simg, verify_simg

class Image:
    """ An image consists of an image type and a filename """

    def __init__(self, image_type, filename, version, daddr,
            force_simg, skip_simg, skip_crc32):
        self.type = image_type
        self.filename = filename
        self.version = version
        self.daddr = daddr
        self.force_simg = force_simg
        self.skip_simg = skip_simg
        self.skip_crc32 = skip_crc32

    def upload(self, work_dir, tftp, slot):
        # Create image
        version = self.version
        daddr = self.daddr
        filename = self.filename

        if self.force_simg or not (self.skip_simg or verify_simg(filename)):
            contents = open(filename).read()
            simg = create_simg(contents, version=version,
                    daddr=daddr, skip_crc32=self.skip_crc32)
            filename = tempfile.mkstemp(".simg", work_dir + "/")[1]
            open(filename, "w").write(simg)

        # Upload to tftp
        basename = os.path.basename(filename)
        tftp.put_file(filename, basename)
        return basename

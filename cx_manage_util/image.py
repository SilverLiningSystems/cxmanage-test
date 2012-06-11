""" Image objects used by the cx_manage_util controller """

import os
import tempfile

from cx_manage_util.simg import create_simg, has_simg

class Image:
    """ An image consists of an image type, a filename, and any info needed
    to build an SIMG out of it. """

    def __init__(self, image_type, filename, version, daddr,
            force_simg, skip_simg, skip_crc32):
        self.type = image_type
        self.filename = filename
        self.version = version
        self.daddr = daddr
        self.force_simg = force_simg
        self.skip_simg = skip_simg
        self.skip_crc32 = skip_crc32

    def upload(self, work_dir, tftp, slot, new_version):
        """ Create and upload an SIMG file """
        filename = self.filename

        # Create new image if necessary
        contents = open(filename).read()
        if self.type == "SPIF":
            start = int(slot.offset, 16)
            end = start + int(slot.size, 16)
            filename = tempfile.mkstemp(".simg", work_dir + "/")[1]
            open(filename, "w").write(contents[start:end])
        elif self.force_simg or not (self.skip_simg or has_simg(contents)):
            # Figure out version and daddr
            version = self.version
            daddr = self.daddr
            if version == None:
                version = new_version
            if daddr == None:
                daddr = int(slot.daddr, 16)

            # Create simg
            simg = create_simg(contents, version=version,
                    daddr=daddr, skip_crc32=self.skip_crc32)
            filename = tempfile.mkstemp(".simg", work_dir + "/")[1]
            open(filename, "w").write(simg)

        # Upload to tftp
        basename = os.path.basename(filename)
        tftp.put_file(filename, basename)
        return basename

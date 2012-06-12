#Copyright 2012 Calxeda, Inc.  All Rights Reserved. 

""" Image objects used by the cx_manage_util controller """

import os
import subprocess
import tempfile

from cxmanage.simg import create_simg, has_simg

class Image:
    """ An image consists of an image type, a filename, and any info needed
    to build an SIMG out of it. """

    def __init__(self, image_type, filename, version, daddr,
            force_simg, skip_simg, skip_crc32):
        self.type = image_type
        self.filename = filename
        self.version = version
        self.daddr = daddr
        self.skip_crc32 = skip_crc32

        if force_simg:
            self.has_simg = False
        elif skip_simg:
            self.has_simg = True
        else:
            contents = open(filename).read()
            self.has_simg = has_simg(contents)

        if not self.valid_type():
            raise ValueError("%s is not a valid %s image" %
                    (os.path.basename(filename), image_type))

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
        elif not self.has_simg:
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

        # Verify image size
        if os.path.getsize(filename) > int(slot.size, 16):
            raise ValueError("%s is too large for slot %i" %
                    (os.path.basename(self.filename), int(slot.slot)))

        # Upload to tftp
        basename = os.path.basename(filename)
        tftp.put_file(filename, basename)
        return basename

    def valid_type(self):
        """ Make sure the file type (reported by the "file" tool) is valid
        for this image type.

        Returns true/false """

        file_type = subprocess.check_output(["file", self.filename]).split()[1]

        if self.type == "SOC_ELF" and file_type == "ELF":
            return True
        elif file_type == "data":
            return True

        return False

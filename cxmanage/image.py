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


""" Image objects used by the cxmanage controller """

import os
import tempfile

from cxmanage import CxmanageError
from cxmanage.simg import create_simg, has_simg, valid_simg, get_simg_contents

class Image:
    """ An image consists of an image type, a filename, and any info needed
    to build an SIMG out of it. """

    def __init__(self, filename, image_type, simg=None,
            priority=None, daddr=None, skip_crc32=False):
        self.filename = filename
        self.type = image_type
        self.priority = priority
        self.daddr = daddr
        self.skip_crc32 = skip_crc32

        if not os.path.exists(filename):
            raise ValueError("File %s does not exist" % filename)

        if simg == None:
            contents = open(filename).read()
            self.simg = has_simg(contents)
        else:
            self.simg = simg

        if not self.verify():
            raise CxmanageError("%s is not a valid %s image" %
                    (os.path.basename(filename), image_type))

    def upload(self, work_dir, tftp, priority, daddr):
        """ Create and upload an SIMG file """
        filename = self.filename

        # Create new image if necessary
        if not self.simg:
            contents = open(filename).read()

            # Figure out priority and daddr
            if self.priority != None:
                priority = self.priority
            if self.daddr != None:
                daddr = self.daddr

            # Create simg
            align = (self.type in ["CDB", "BOOT_LOG"])
            simg = create_simg(contents, priority=priority, daddr=daddr,
                    skip_crc32=self.skip_crc32, align=align)
            filename = tempfile.mkstemp(".simg", work_dir + "/")[1]
            open(filename, "w").write(simg)

        # Make sure the simg was built correctly
        if not valid_simg(open(filename).read()):
            raise CxmanageError("%s is not a valid SIMG" %
                    os.path.basename(self.filename))

        # Upload to tftp
        basename = os.path.basename(filename)
        tftp.put_file(filename, basename)
        return basename

    def size(self):
        """ Return the full size of this image (as an SIMG) """
        if self.simg:
            return os.path.getsize(self.filename)
        else:
            contents = open(self.filename).read()
            align = (self.type in ["CDB", "BOOT_LOG"])
            simg = create_simg(contents, skip_crc32=True, align=align)
            return len(simg)

    def verify(self):
        """ Return true if the image is valid, false otherwise """

        if self.type in ["CDB", "BOOT_LOG"]:
            # Look for "CDBH"
            contents = open(self.filename).read()
            if self.simg:
                contents = get_simg_contents(contents)

            return contents[:4] == "CDBH"

        return True

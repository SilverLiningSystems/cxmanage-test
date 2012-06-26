#Copyright 2012 Calxeda, Inc.  All rights reserved.

"""python for manipulating Calxeda SIMG headers"""

import struct

from cxmanage.crc32 import get_crc32

class SIMGHeader:
    """ Container for an SIMG header """

    def __init__(self, header_string=None):
        if header_string == None:
            self.magic_string = 'SIMG'
            self.hdrfmt = 0
            self.version = 0
            self.imgoff = 28
            self.imglen = 0
            self.daddr = 0
            self.flags = 0
            self.crc32 = 0
        else:
            tup = struct.unpack('<4sHHIIIII', header_string)
            self.magic_string = tup[0]
            self.hdrfmt = tup[1]
            self.version = tup[2]
            self.imgoff = tup[3]
            self.imglen = tup[4]
            self.daddr = tup[5]
            self.flags = tup[6]
            self.crc32 = tup[7]

    def __str__(self):
        return struct.pack('<4sHHIIIII',
                self.magic_string,
                self.hdrfmt,
                self.version,
                self.imgoff,
                self.imglen,
                self.daddr,
                self.flags,
                self.crc32)


def create_simg(contents, version=0, daddr=0, skip_crc32=False):
    """Create an SIMG version of a file

    Assumes version and hdrfmt are 0.
    """

    header = SIMGHeader()
    header.version = version
    header.imglen = len(contents)
    header.daddr = daddr

    # Calculate crc value
    if skip_crc32:
        crc32 = 0
    else:
        crc32 = get_crc32(contents, get_crc32(str(header)))

    # Get SIMG header
    header.flags = 0xFFFFFFFF
    header.crc32 = crc32

    return str(header) + contents


def has_simg(simg):
    """Return true if this string has an SIMG header"""

    if len(simg) < 28:
        return False
    header = SIMGHeader(simg[:28])

    # Check for magic word
    return header.magic_string == 'SIMG'


def valid_simg(simg):
    """Return true if this is a valid SIMG"""

    if not has_simg(simg):
        return False
    header = SIMGHeader(simg[:28])
    contents = simg[28:]

    # Check offset
    if header.imgoff != 28:
        return False

    # Check length
    if len(contents) < header.imglen:
        return False

    # Check crc32
    crc32 = header.crc32
    if crc32 != 0:
        header.flags = 0
        header.crc32 = 0
        if crc32 != get_crc32(contents, get_crc32(str(header))):
            return False

    return True


def get_simg_header(simg):
    """ Return the header of this SIMG """
    if len(simg) < 28 or not has_simg(simg):
        raise ValueError("Failed to read invalid SIMG")

    return SIMGHeader(simg[:28])

#Copyright 2012 Calxeda, Inc.  All rights reserved.

"""python for manipulating Calxeda SIMG headers"""

import struct

from cxmanage.crc32 import get_crc32

def create_simg(contents, version=0, daddr=0, skip_crc32=False):
    """Create an SIMG version of a file

    Assumes version and hdrfmt are 0.
    """

    # Calculate crc value
    if skip_crc32:
        crc32 = 0
    else:
        string = struct.pack('<4sHHIIIII',
                'SIMG',         #magic_string
                0,              #hdrfmt
                version,        #version
                28,             #imgoff
                len(contents),  #imglen
                daddr,          #daddr
                0x00000000,     #flags
                0x00000000)     #crc32
        crc32 = get_crc32(contents, get_crc32(string))

    # Get SIMG header
    string = struct.pack('<4sHHIIIII',
            'SIMG',         #magic_string
            0,              #hdrfmt
            version,        #version
            28,             #imgoff
            len(contents),  #imglen
            daddr,          #daddr
            0xffffffff,     #flags
            crc32)          #crc32

    return string + contents

def has_simg(simg):
    """Return true if infile has an SIMG header"""
    # Bail early if the file is too small
    if len(simg) < 28:
        return False

    header = simg[:28]
    tup = struct.unpack('<4sHHIIIII', header)

    # Magic word
    if tup[0] != "SIMG":
        return False

    return True

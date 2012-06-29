import struct

from cxmanage.crc32 import get_crc32

class UbootEnv:
    """ A uboot environment consisting of variables and their assignments. """

    def __init__(self, contents):
        """ Load a uboot environment from a binary string """
        self.size = len(contents)
        self.variables = {}

        contents = contents.rstrip("%c%c" % (chr(0), chr(255)))[4:]
        lines = contents.split(chr(0))
        for line in lines:
            part = line.partition("=")
            self.variables[part[0]] = part[2]

    def get_variable(self, variable):
        """ Get a variable from the uboot environment """
        if variable in self.variables:
            return self.variables[variable]
        else:
            return None

    def set_variable(self, variable, value):
        """ Set a variable in the uboot environment """
        self.variables[variable] = value

    def __str__(self):
        """ Return a binary string for the uboot environment """

        # TODO: figure out crc32 -- it uses a different algorithm than we have
        crc32 = 0
        contents = struct.pack("<I", crc32)

        # Add variables
        for variable in self.variables:
            contents += "%s=%s\0" % (variable, self.variables[variable])
        contents += "\0"

        # Pad
        contents += "".join([chr(255)
                for a in range(self.size - len(contents))])

        return contents


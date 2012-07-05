import struct

from crc32 import get_crc32

ENVIRONMENT_SIZE = 8192

class UbootEnv:
    """ A uboot environment consisting of variables and their assignments. """

    def __init__(self, contents):
        """ Load a uboot environment from a binary string """
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

    def set_boot_order(self, boot_args, retry=False):
        """ Set the boot order specified in the uboot environment.

        Here are the valid boot arguments:

        pxe: boot from pxe server
        disk: boot from default sata drive
        disk#: boot from numbered sata drive
        """
        command = ["run bootcmd_setup"]
        for arg in boot_args:
            if arg == "pxe":
                command.append("run bootcmd_pxe")
            elif arg == "disk":
                command.append("run bootcmd_sata")
            elif arg.startswith("disk"):
                command.append("setenv bootdevice %i" % int(args[4:]))
                command.append("run bootcmd_sata")
            else:
                raise ValueError("Invalid boot argument %s" % arg)

        if retry:
            # Set the "retry" variable
            retry_command = ["sleep 1", command[-1], "run bootcmd_retry"]
            self.set_variable("bootcmd_retry", "; ".join(retry_command))

            command.append("run bootcmd_retry")

        self.set_variable("bootcmd0", "; ".join(command))

    def __str__(self):
        """ Return a raw string representation of the uboot environment """

        contents = ""

        # Add variables
        for variable in self.variables:
            contents += "%s=%s\0" % (variable, self.variables[variable])
        contents += "\0"

        # Add padding to end
        contents += "".join([chr(255)
                for a in range(ENVIRONMENT_SIZE - len(contents) - 4)])

        # Add crc32 to beginning
        crc32 = get_crc32(contents, 0xFFFFFFFF) ^ 0xFFFFFFFF
        contents = struct.pack("<I", crc32) + contents

        return contents


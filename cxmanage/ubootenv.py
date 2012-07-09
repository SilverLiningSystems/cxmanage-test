#Copyright 2012 Calxeda, Inc.  All Rights Reserved.

import struct

from cxmanage import CxmanageError
from cxmanage.crc32 import get_crc32

ENVIRONMENT_SIZE = 8192

class UbootEnv:
    """ A uboot environment consisting of variables and their assignments. """

    def __init__(self, contents=None):
        """ Load a uboot environment from a binary string """
        self.variables = {}

        if contents != None:
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

    def set_boot_order(self, boot_args):
        """ Set the boot order specified in the uboot environment.

        Here are the valid boot arguments:

        pxe: boot from pxe server
        disk: boot from default sata drive
        disk#: boot from numbered sata drive
        """
        commands = ["run bootcmd_setup"]
        retry = False
        reset = False
        for arg in boot_args:
            if arg == "pxe":
                commands.append("run bootcmd_pxe")
            elif arg == "disk":
                commands.append("run bootcmd_sata")
            elif arg.startswith("disk"):
                commands.append("setenv bootdevice %i && run bootcmd_sata"
                        % int(arg[4:]))
            elif arg == "retry":
                retry = True
            elif arg == "reset":
                reset = True
            else:
                raise ValueError("Invalid boot argument %s" % arg)

        if retry and reset:
            raise ValueError("retry and reset are mutually exclusive")
        elif retry:
            commands[-1] = "while true\ndo\n%s\nsleep 1\ndone" % commands[-1]
        elif reset:
            commands.append("reset")

        self.set_variable("bootcmd0", "; ".join(commands))

    def get_boot_order(self):
        """ Get the boot order specified in the uboot environment. """

        commands = self.get_variable("bootcmd0").split("; ")
        boot_args = []

        retry = False
        for command in commands:
            if command.startswith("while true"):
                retry = True
                command = command.split("\n")[2]

            if command == "run bootcmd_setup":
                pass
            elif command == "run bootcmd_pxe":
                boot_args.append("pxe")
            elif command == "run bootcmd_sata":
                boot_args.append("disk")
            elif command.startswith("setenv bootdevice"):
                boot_args.append("disk%i" % int(command.split()[2]))
            elif command == "reset":
                boot_args.append("reset")
                break
            else:
                raise CxmanageError("Unrecognized boot command: %s" % command)

            if retry:
                boot_args.append("retry")
                break

        if len(boot_args) == 0:
            boot_args.append("none")

        return boot_args

    def get_contents(self):
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


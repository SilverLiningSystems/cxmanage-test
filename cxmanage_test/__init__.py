#Copyright 2012 Calxeda, Inc.  All Rights Reserved.

""" Various objects used by tests """

import random
import tempfile

class TestSlot:
    """ Slot info for a partition """
    def __init__(self, slot=0, slot_type=2, offset=0,
            size=0, version=0, daddr=0, in_use=None):
        self.slot = "%2i" % slot
        self.type = {
                2: "02 (S2_ELF)",
                3: "03 (SOC_ELF)",
                10: "0a (CDB)"
            }[slot_type]
        self.offset = "%8x" % offset
        self.size = "%8x" % size
        self.version = "%8x" % version
        self.daddr = "%8x" % daddr
        self.in_use = {None: "Unknown", True: "1", False: "0"}[in_use]

class TestSensor:
    """ Sensor result from bmc/target """
    def __init__(self, sensor_name, sensor_reading):
        self.sensor_name = sensor_name
        self.sensor_reading = sensor_reading

def random_file(work_dir, size):
    """ Create a random file """
    contents = "".join([chr(random.randint(0, 255))
        for a in range(size)])
    filename = tempfile.mkstemp(prefix="%s/" % work_dir)[1]
    open(filename, "w").write(contents)
    return filename

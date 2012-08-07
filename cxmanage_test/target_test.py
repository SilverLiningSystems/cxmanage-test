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


import random
import shutil
import tempfile
import unittest

from pyipmi.bmc import LanBMC

from cxmanage.simg import create_simg
from cxmanage.target import Target
from cxmanage.tftp import InternalTftp, ExternalTftp
from cxmanage.ubootenv import UbootEnv

from cxmanage_test import TestImage, TestSensor

NUM_NODES = 4
ADDRESSES = ["192.168.100.%i" % x for x in range(1, NUM_NODES+1)]

class TargetTest(unittest.TestCase):
    """ Tests involving cxmanage targets """

    def setUp(self):
        self.work_dir = tempfile.mkdtemp(prefix="cxmanage_test-")

        self.targets = [Target(x, verbosity=0, bmc_class=DummyBMC,
                ubootenv_class=DummyUbootEnv) for x in ADDRESSES]

        # Set up an internal server
        self.tftp = InternalTftp()

    def tearDown(self):
        shutil.rmtree(self.work_dir)

    def test_get_ipinfo(self):
        """ Test target.get_ipinfo method """
        for target in self.targets:
            result = target.get_ipinfo(self.tftp)

            self.assertEqual(target.bmc.executed, ["get_fabric_ipinfo"])
            self.assertEqual(result, [(i, ADDRESSES[i])
                    for i in range(NUM_NODES)])

    def test_get_power(self):
        """ Test target.get_power method """
        for target in self.targets:
            result = target.get_power()

            self.assertEqual(target.bmc.executed, ["get_chassis_status"])
            self.assertEqual(result, False)

    def test_set_power(self):
        """ Test target.set_power method """
        for target in self.targets:
            modes = ["off", "on", "reset", "off"]
            for mode in modes:
                target.set_power(mode)

            self.assertEqual(target.bmc.executed,
                    [("set_chassis_power", x) for x in modes])

    def test_get_power_policy(self):
        """ Test target.get_power_policy method """
        for target in self.targets:
            result = target.get_power_policy()

            self.assertEqual(target.bmc.executed, ["get_chassis_status"])
            self.assertEqual(result, "always-off")

    def test_set_power_policy(self):
        """ Test target.set_power_policy method """
        for target in self.targets:
            modes = ["always-on", "previous", "always-off"]
            for mode in modes:
                target.set_power_policy(mode)

            self.assertEqual(target.bmc.executed,
                    [("set_chassis_policy", x) for x in modes])

    def test_get_sensors(self):
        """ Test target.get_sensors method """
        for target in self.targets:
            result = target.get_sensors()

            self.assertEqual(target.bmc.executed, ["sdr_list"])

            self.assertEqual(len(result), 2)
            self.assertEqual(result[0].sensor_name, "Node Power")
            self.assertTrue(result[0].sensor_reading.endswith("Watts"))
            self.assertEqual(result[1].sensor_name, "Board Temp")
            self.assertTrue(result[1].sensor_reading.endswith("degrees C"))

    def test_update_firmware(self):
        """ Test target.update_firmware method """
        filename = "%s/%s" % (self.work_dir, "image.bin")
        open(filename, "w").write("")

        images = [
            TestImage(filename, "SOC_ELF"),
            TestImage(filename, "CDB"),
            TestImage(filename, "UBOOTENV")
        ]

        for target in self.targets:
            target.update_firmware(self.tftp, images)

            partitions = target.bmc.partitions
            unchanged_partitions = [partitions[x] for x in [0, 1, 4]]
            changed_partitions = [partitions[x] for x in [2, 3, 6]]
            ubootenv_partition = partitions[5]

            for partition in unchanged_partitions:
                self.assertEqual(partition.updates, 0)
                self.assertEqual(partition.retrieves, 0)
                self.assertEqual(partition.checks, 0)
                self.assertEqual(partition.activates, 0)

            for partition in changed_partitions:
                self.assertEqual(partition.updates, 1)
                self.assertEqual(partition.retrieves, 0)
                self.assertEqual(partition.checks, 1)
                self.assertEqual(partition.activates, 1)

            self.assertEqual(ubootenv_partition.updates, 1)
            self.assertEqual(ubootenv_partition.retrieves, 1)
            self.assertEqual(ubootenv_partition.checks, 1)
            self.assertEqual(ubootenv_partition.activates, 1)

    def test_config_reset(self):
        """ Test target.config_reset method """
        for target in self.targets:
            target.config_reset(self.tftp)

            # Assert config reset
            executed = target.bmc.executed
            self.assertEqual(
                    len([x for x in executed if x == "reset_firmware"]), 1)

            # Assert sel clear
            self.assertEqual(
                    len([x for x in executed if x == "sel_clear"]), 1)

            # Assert ubootenv changes
            active = target.bmc.partitions[5]
            inactive = target.bmc.partitions[6]
            self.assertEqual(active.updates, 1)
            self.assertEqual(active.retrieves, 0)
            self.assertEqual(active.checks, 1)
            self.assertEqual(active.activates, 1)
            self.assertEqual(inactive.updates, 0)
            self.assertEqual(inactive.retrieves, 1)
            self.assertEqual(inactive.checks, 0)
            self.assertEqual(inactive.activates, 0)

    def test_set_boot_order(self):
        """ Test target.set_boot_order method """
        boot_args = ["disk", "pxe", "retry"]
        for target in self.targets:
            target.set_boot_order(self.tftp, boot_args)

            partitions = target.bmc.partitions
            ubootenv_partition = partitions[5]
            unchanged_partitions = [x for x in partitions
                    if x != ubootenv_partition]

            self.assertEqual(ubootenv_partition.updates, 1)
            self.assertEqual(ubootenv_partition.retrieves, 1)
            self.assertEqual(ubootenv_partition.checks, 1)
            self.assertEqual(ubootenv_partition.activates, 1)

            for partition in unchanged_partitions:
                self.assertEqual(partition.updates, 0)
                self.assertEqual(partition.retrieves, 0)
                self.assertEqual(partition.checks, 0)
                self.assertEqual(partition.activates, 0)

    def test_get_boot_order(self):
        """ Test target.get_boot_order method """
        for target in self.targets:
            result = target.get_boot_order(self.tftp)

            partitions = target.bmc.partitions
            ubootenv_partition = partitions[5]
            unchanged_partitions = [x for x in partitions
                    if x != ubootenv_partition]

            self.assertEqual(ubootenv_partition.updates, 0)
            self.assertEqual(ubootenv_partition.retrieves, 1)
            self.assertEqual(ubootenv_partition.checks, 0)
            self.assertEqual(ubootenv_partition.activates, 0)

            for partition in unchanged_partitions:
                self.assertEqual(partition.updates, 0)
                self.assertEqual(partition.retrieves, 0)
                self.assertEqual(partition.checks, 0)
                self.assertEqual(partition.activates, 0)

            self.assertEqual(result, ["disk", "pxe"])

    def test_info_basic(self):
        """ Test target.info_basic method """
        for target in self.targets:
            result = target.info_basic()

            self.assertEqual(target.bmc.executed, ["info_basic"])
            for attr in ["header", "version", "build_number", "timestamp"]:
                self.assertTrue(hasattr(result, attr))

class DummyBMC(LanBMC):
    """ Dummy BMC for the target tests """
    def __init__(self, **kwargs):
        LanBMC.__init__(self, **kwargs)

        self.executed = []

        self.partitions = [
                Partition(0, 3, 0, 393216, in_use=True),        # socman
                Partition(1, 10, 393216, 196608),               # factory cdb
                Partition(2, 3, 589824, 393216, in_use=False),  # socman
                Partition(3, 10, 983040, 196608),               # factory cdb
                Partition(4, 10, 1179648, 196608),              # running cdb
                Partition(5, 11, 1376256, 12288),               # ubootenv
                Partition(6, 11, 1388544, 12288)                # ubootenv
        ]

    def get_fabric_ipinfo(self, filename, tftp_address):
        """ Upload an ipinfo file from the node to TFTP"""
        self.executed.append("get_fabric_ipinfo")

        work_dir = tempfile.mkdtemp(prefix="cxmanage_test-")

        # Create IP info file
        ipinfo = open("%s/%s" % (work_dir, filename), "w")
        for i in range(len(ADDRESSES)):
            ipinfo.write("Node %i: %s\n" % (i, ADDRESSES[i]))
        ipinfo.close()

        # Upload to tftp
        address, port = tftp_address.split(":")
        port = int(port)
        tftp = ExternalTftp(address, port)
        tftp.put_file("%s/%s" % (work_dir, filename), filename)

        shutil.rmtree(work_dir)

    def set_chassis_power(self, mode):
        """ Set chassis power """
        self.executed.append(("set_chassis_power", mode))

    def get_chassis_status(self):
        """ Get chassis status """
        self.executed.append("get_chassis_status")

        class Result:
            def __init__(self):
                self.power_on = False
                self.power_restore_policy = "always-off"
        return Result()

    def set_chassis_policy(self, mode):
        """ Set chassis restore policy """
        self.executed.append(("set_chassis_policy", mode))

    def mc_reset(self, mode):
        """ Reset the MC """
        self.executed.append(("mc_reset", mode))

    def reset_firmware(self):
        """ Reset the running CDB """
        self.executed.append("reset_firmware")

    def sel_clear(self):
        """ Clear SEL """
        self.executed.append("sel_clear")

    def get_firmware_info(self):
        """ Get partition and simg info """
        self.executed.append("get_firmware_info")

        return [x.fwinfo for x in self.partitions]

    def update_firmware(self, filename, slot_id, image_type, tftp_address):
        """ Download a file from a TFTP server to a given slot.

        Make sure the image type matches. """
        self.executed.append(("update_firmware", filename,
                slot_id, image_type, tftp_address))
        self.partitions[slot_id].updates += 1

        class Result:
            def __init__(self):
                self.tftp_handle_id = 0
        return Result()

    def retrieve_firmware(self, filename, slot_id, image_type, tftp_address):
        self.executed.append(("retrieve_firmware", filename,
                slot_id, image_type, tftp_address))
        self.partitions[slot_id].retrieves += 1

        # Upload blank image to tftp
        work_dir = tempfile.mkdtemp(prefix="cxmanage_test-")
        open("%s/%s" % (work_dir, filename), "w").write(create_simg(""))
        address, port = tftp_address.split(":")
        port = int(port)
        tftp = ExternalTftp(address, port)
        tftp.put_file("%s/%s" % (work_dir, filename), filename)
        shutil.rmtree(work_dir)

        class Result:
            def __init__(self):
                self.tftp_handle_id = 0
        return Result()

    def get_firmware_status(self, handle):
        self.executed.append("get_firmware_status")

        class Result:
            def __init__(self):
                self.status = "Complete"
        return Result()

    def check_firmware(self, slot_id):
        self.executed.append(("check_firmware", slot_id))
        self.partitions[slot_id].checks += 1

        class Result:
            def __init__(self):
                self.crc32 = 0
                self.error = None
        return Result()

    def activate_firmware(self, slot_id):
        self.executed.append(("activate_firmware", slot_id))
        self.partitions[slot_id].activates += 1

    def sdr_list(self):
        """ Get sensor info from the node. """
        self.executed.append("sdr_list")

        power_value = "%f (+/- 0) Watts" % random.uniform(0, 10)
        temp_value = "%f (+/- 0) degrees C" % random.uniform(30, 50)
        sensors = [
                TestSensor("Node Power", power_value),
                TestSensor("Board Temp", temp_value)
        ]

        return sensors

    def get_info_basic(self):
        """ Get basic SoC info from this node """
        self.executed.append("info_basic")

        class Result:
            def __init__(self):
                self.header = "Calxeda SoC (0x0096CD)"
                self.version = "0.0.0"
                self.build_number = "00000000"
                self.timestamp = "0"
        return Result()

class Partition:
    def __init__(self, slot, slot_type, offset=0,
            size=0, version=0, daddr=0, in_use=None):
        self.updates = 0
        self.retrieves = 0
        self.checks = 0
        self.activates = 0
        self.fwinfo = FWInfoEntry(slot, slot_type, offset,
                size, version, daddr, in_use)

class FWInfoEntry:
    """ Firmware info for a single partition """
    def __init__(self, slot, slot_type, offset=0,
            size=0, version=0, daddr=0, in_use=None):
        self.slot = "%2i" % slot
        self.type = {
                2: "02 (S2_ELF)",
                3: "03 (SOC_ELF)",
                10: "0a (CDB)",
                11: "0b (UBOOTENV)"
            }[slot_type]
        self.offset = "%8x" % offset
        self.size = "%8x" % size
        self.version = "%8x" % version
        self.daddr = "%8x" % daddr
        self.in_use = {None: "Unknown", True: "1", False: "0"}[in_use]
        self.flags = "fffffffd"

class DummyUbootEnv(UbootEnv):
    def get_boot_order(self):
        return ["disk", "pxe"]

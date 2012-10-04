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
import time
import unittest

from cxmanage.controller import Controller
from cxmanage.ubootenv import UbootEnv
from cxmanage_test import TestSensor

NUM_NODES = 128
ADDRESSES = ["192.168.100.%i" % x for x in range(1, NUM_NODES+1)]

class ControllerTest(unittest.TestCase):
    """ Test the cxmanage controller """

    def setUp(self):
        # Set up the controller
        self.controller = Controller(max_threads=32,
                image_class=DummyImage, target_class=DummyTarget)

    def test_add_targets(self):
        """ Test adding targets"""
        # Add targets
        self.assertEqual(len(self.controller.targets), 0)
        for address in ADDRESSES:
            self.controller.add_target(address, "admin", "admin")

        # Examine targets
        self.assertEqual(len(ADDRESSES), len(self.controller.targets))
        for address in ADDRESSES:
            self.assertTrue(any([address == x.address
                    for x in self.controller.targets]))

    def test_add_all_targets(self):
        """ Test adding targets with ipinfo """
        # Add targets
        self.assertEqual(len(self.controller.targets), 0)
        self.controller.add_fabrics([ADDRESSES[0]], "admin", "admin")

        # Examine targets
        self.assertEqual(len(ADDRESSES), len(self.controller.targets))
        for address in ADDRESSES:
            self.assertTrue(any([address == x.address
                    for x in self.controller.targets]))

    def test_add_images(self):
        """ Test adding images """
        # Add images
        self.assertEqual(len(self.controller.images), 0)
        self.controller.add_image("stage2boot.bin", "S2_ELF")
        self.controller.add_image("socmanager.elf", "SOC_ELF")
        self.controller.add_image("factory.cdb", "CDB")

        # Examine images
        self.assertEqual(len(self.controller.images), 3)
        s2_image = self.controller.images[0]
        soc_image = self.controller.images[1]
        cdb_image = self.controller.images[2]
        self.assertEqual(s2_image.filename, "stage2boot.bin")
        self.assertEqual(s2_image.type, "S2_ELF")
        self.assertEqual(soc_image.filename, "socmanager.elf")
        self.assertEqual(soc_image.type, "SOC_ELF")
        self.assertEqual(cdb_image.filename, "factory.cdb")
        self.assertEqual(cdb_image.type, "CDB")

class ControllerCommandTest(unittest.TestCase):
    """ Test the various controller commands """
    def setUp(self):
        # Set up the controller and add targets
        self.controller = Controller(max_threads=32,
                image_class=DummyImage, target_class=DummyTarget)
        self.controller.add_fabrics([ADDRESSES[0]], "admin", "admin")

    def test_command_delay(self):
        """Test that we delay for at least command_delay"""
        orig_delay = self.controller.command_delay
        orig_targets = self.controller.targets
        try:
            delay = random.randint(1, 5)
            self.controller.command_delay = delay
            self.controller.targets = [orig_targets[0]]
            start = time.time()
            self.controller.power_status()
            finish = time.time()
            self.assertLess(delay, finish - start)
        finally:
            self.controller.command_delay = orig_delay
            self.controller.targets = orig_targets

    def test_power(self):
        """ Test power command """
        # Send power commands
        modes = ["on", "reset", "off"]
        for mode in modes:
            self.assertFalse(self.controller.power(mode))

        # Verify commands
        for target in self.controller.targets:
            self.assertEqual(target.executed,
                    [("set_power", x) for x in modes])

    def test_power_status(self):
        """ Test power status command """
        # Send power status command
        self.assertFalse(self.controller.power_status())

        # Verify command
        for target in self.controller.targets:
            self.assertEqual(target.executed, ["get_power"])

    def test_power_policy(self):
        """ Test power policy command """
        # Send power policy commands
        modes = ["always-on", "previous", "always-off"]
        for mode in modes:
            self.assertFalse(self.controller.power_policy(mode))

        # Verify commands
        for target in self.controller.targets:
            self.assertEqual(target.executed,
                    [("set_power_policy", x) for x in modes])

    def test_power_policy_status(self):
        """ Test power policy status command """
        # Send power policy status command
        self.assertFalse(self.controller.power_policy_status())

        # Verify command
        for target in self.controller.targets:
            self.assertEqual(target.executed, ["get_power_policy"])

    def test_mc_reset(self):
        """ Test mc reset command """
        # Send mc reset command
        self.assertFalse(self.controller.mc_reset())

        # Verify command
        for target in self.controller.targets:
            self.assertEqual(target.executed, ["mc_reset"])

    def test_get_sensors(self):
        """ Test get sensors command """
        # Send get sensors commands
        self.assertFalse(self.controller.get_sensors())
        self.assertFalse(self.controller.get_sensors("Node Power"))

        # Verify command
        for target in self.controller.targets:
            self.assertTrue(len(target.executed), 2)
            self.assertTrue(all([x == "get_sensors" for x in target.executed]))

    def test_get_ipinfo(self):
        """ Test get ipinfo command """
        # Send get ipinfo command
        self.assertFalse(self.controller.get_ipinfo())

        # Verify command
        for target in self.controller.targets:
            self.assertEqual(target.executed, ["get_ipinfo"])

    def test_get_macaddrs(self):
        """ Test get macaddrs command """
        # Send get macaddrs command
        self.assertFalse(self.controller.get_macaddrs())

        # Verify command
        for target in self.controller.targets:
            self.assertEqual(target.executed, ["get_macaddrs"])

    def test_config_reset(self):
        """ Test config reset command """
        # Send config reset command
        self.assertFalse(self.controller.config_reset())

        # Verify command
        for target in self.controller.targets:
            self.assertEqual(target.executed, ["config_reset"])

    def test_config_boot(self):
        """ Test config boot command """
        # Send config boot command
        boot_args = ["disk", "pxe", "retry"]
        self.assertFalse(self.controller.config_boot(boot_args))

        # Verify command
        for target in self.controller.targets:
            self.assertEqual(target.executed, [("set_boot_order", boot_args)])

    def test_config_boot_status(self):
        """ Test config boot status command """
        # Send config boot status command
        self.assertFalse(self.controller.config_boot_status())

        # Verify command
        for target in self.controller.targets:
            self.assertEqual(target.executed, ["get_boot_order"])

    def test_ipmitool_command(self):
        """ Test ipmitool command """
        # Send ipmitool command
        ipmitool_args = ["chassis", "status"]
        self.assertFalse(self.controller.ipmitool_command(ipmitool_args))

        # Verify command
        for target in self.controller.targets:
            self.assertEqual(target.executed,
                    [("ipmitool_command", ipmitool_args)])

    def test_update_firmware(self):
        """ Test fwupdate command """
        # Add images
        self.controller.add_image("stage2boot.bin", "S2_ELF")
        self.controller.add_image("socmanager.elf", "SOC_ELF")
        self.controller.add_image("factory.cdb", "CDB")

        # Perform firmware update
        self.assertFalse(self.controller.update_firmware())

        # Check updated types
        for target in self.controller.targets:
            self.assertEqual(len(target.executed), 2)
            self.assertEqual(target.executed[0], "check_firmware")
            self.assertEqual(target.executed[1][0], "update_firmware")
            updated_types = [x.type for x in target.executed[1][1]]
            for image_type in ["S2_ELF", "SOC_ELF", "CDB"]:
                self.assertTrue(image_type in updated_types)

    def test_info_basic(self):
        """ Test info basic command """
        # Send config boot status command
        self.assertFalse(self.controller.info_basic())

        # Verify command
        for target in self.controller.targets:
            self.assertEqual(target.executed, ["info_basic"])

    def test_info_ubootenv(self):
        """ Test info ubootenv command """
        # Send config boot status command
        self.assertFalse(self.controller.info_ubootenv())

        # Verify command
        for target in self.controller.targets:
            self.assertEqual(target.executed, ["get_ubootenv"])

    def test_info_dump(self):
        """ Test info dump command """
        # Send mc reset command
        self.assertFalse(self.controller.info_dump())

        # Verify command
        for target in self.controller.targets:
            self.assertEqual(target.executed, ["info_dump"])


class DummyTarget:
    """ Dummy target for the controller tests """
    def __init__(self, address, *args):
        self.address = address
        self.executed = []

    def get_ipinfo(self, tftp):
        self.executed.append("get_ipinfo")
        return list(enumerate(ADDRESSES))

    def get_macaddrs(self, tftp):
        self.executed.append("get_macaddrs")
        result = []
        for node in range(NUM_NODES):
            for port in range(3):
                address = "00:00:00:00:%02x:%02x" % (node, port)
                result.append((node, port, address))
        return result

    def get_power(self):
        self.executed.append("get_power")
        return False

    def set_power(self, mode):
        self.executed.append(("set_power", mode))

    def get_power_policy(self):
        self.executed.append("get_power_policy")
        return "always-off"

    def set_power_policy(self, mode):
        self.executed.append(("set_power_policy", mode))

    def mc_reset(self):
        self.executed.append("mc_reset")

    def check_firmware(self, required_socman_version, firmware_config):
        self.executed.append("check_firmware")

    def update_firmware(self, tftp, images, partition_arg, firmware_version):
        self.executed.append(("update_firmware", images))
        time.sleep(random.randint(0, 2))

    def get_sensors(self, name=""):
        self.executed.append("get_sensors")
        power_value = "%f (+/- 0) Watts" % random.uniform(0, 10)
        temp_value = "%f (+/- 0) degrees C" % random.uniform(30, 50)
        sensors = [
                TestSensor("Node Power", power_value),
                TestSensor("Board Temp", temp_value)
        ]
        return [x for x in sensors if name.lower() in x.sensor_name.lower()]

    def config_reset(self, tftp):
        self.executed.append("config_reset")

    def set_boot_order(self, tftp, boot_args):
        self.executed.append(("set_boot_order", boot_args))

    def get_boot_order(self, tftp):
        self.executed.append("get_boot_order")
        return ["disk", "pxe"]

    def info_basic(self):
        self.executed.append("info_basic")

        class Result:
            def __init__(self):
                self.header = "Calxeda SoC (0x0096CD)"
                self.card = "TestBoard X00"
                self.version = "v0.0.0"
                self.build_number = "00000000"
                self.timestamp = "0"
                self.soc_version = "0.0.0"
                self.a9boot_version = "0.0.0"
                self.uboot_version = "0.0.0"
        return Result()

    def info_dump(self, tftp):
        self.executed.append("info_dump")

    def ipmitool_command(self, ipmitool_args):
        self.executed.append(("ipmitool_command", ipmitool_args))
        return "Dummy output"

    def get_ubootenv(self, tftp):
        self.executed.append("get_ubootenv")

        ubootenv = UbootEnv()
        ubootenv.variables["bootcmd0"] = "run bootcmd_default"
        ubootenv.variables["bootcmd_default"] = "run bootcmd_sata"
        return ubootenv

class DummyImage:
    def __init__(self, filename, image_type, *args):
        self.filename = filename
        self.type = image_type


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

from cxmanage_api.fabric import Fabric
from cxmanage_api.tftp import InternalTftp, ExternalTftp
from cxmanage_api.firmware_package import FirmwarePackage
from cxmanage_api.ubootenv import UbootEnv
from cxmanage_test import TestSensor

NUM_NODES = 128
ADDRESSES = ["192.168.100.%i" % x for x in range(1, NUM_NODES+1)]

class FabricTest(unittest.TestCase):
    """ Test the various Fabric commands """
    def setUp(self):
        # Set up the controller and add targets
        self.fabric = Fabric("192.168.100.1", max_threads=32,
                node=DummyNode)
        self.nodes = [DummyNode(x) for x in ADDRESSES]
        self.fabric._nodes = dict((i, self.nodes[i])
                for i in xrange(NUM_NODES))

    def test_tftp(self):
        """ Test the tftp property """
        tftp = InternalTftp()
        self.fabric.tftp = tftp
        self.assertTrue(self.fabric.tftp is tftp)
        for node in self.nodes:
            self.assertTrue(node.tftp is tftp)

        tftp = ExternalTftp("127.0.0.1")
        self.fabric.tftp = tftp
        self.assertTrue(self.fabric.tftp is tftp)
        for node in self.nodes:
            self.assertTrue(node.tftp is tftp)

    def test_command_delay(self):
        """Test that we delay for at least command_delay"""
        delay = random.randint(1, 5)
        self.fabric.command_delay = delay
        self.fabric._nodes = {0: self.fabric.nodes[0]}
        start = time.time()
        self.fabric.info_basic()
        finish = time.time()
        self.assertLess(delay, finish - start)

    def test_get_mac_addresses(self):
        """ Test get_mac_addresses command """
        self.fabric.get_mac_addresses()
        for node in self.nodes:
            self.assertEqual(node.executed, ["get_mac_addresses"])

    def test_get_sensors(self):
        """ Test get_sensors command """
        self.fabric.get_sensors()
        self.fabric.get_sensors("Node Power")
        for node in self.nodes:
            self.assertEqual(node.executed, ["get_sensors", "get_sensors"])

    def test_get_firmware_info(self):
        """ Test get_firmware_info command """
        self.fabric.get_firmware_info()
        for node in self.nodes:
            self.assertEqual(node.executed, ["get_firmware_info"])

    def test_is_updatable(self):
        """ Test is_updatable command """
        package = FirmwarePackage()
        self.fabric.is_updatable(package)
        for node in self.nodes:
            self.assertEqual(node.executed, [("is_updatable", package)])

    def test_update_firmware(self):
        """ Test update_firmware command """
        package = FirmwarePackage()
        self.fabric.update_firmware(package)
        for node in self.nodes:
            self.assertEqual(node.executed, [("update_firmware", package)])

    def test_config_reset(self):
        """ Test config_reset command """
        self.fabric.config_reset()
        for node in self.nodes:
            self.assertEqual(node.executed, ["config_reset"])

    def test_set_boot_order(self):
        """ Test set_boot_order command """
        boot_args = "disk0,pxe,retry"
        self.fabric.set_boot_order(boot_args)
        for node in self.nodes:
            self.assertEqual(node.executed, [("set_boot_order", boot_args)])

    def test_get_boot_order(self):
        """ Test get_boot_order command """
        self.fabric.get_boot_order()
        for node in self.nodes:
            self.assertEqual(node.executed, ["get_boot_order"])

    def test_info_basic(self):
        """ Test info_basic command """
        self.fabric.info_basic()
        for node in self.nodes:
            self.assertEqual(node.executed, ["info_basic"])

    def test_info_dump(self):
        """ Test info_dump command """
        self.fabric.info_dump()
        for node in self.nodes:
            self.assertEqual(node.executed, ["info_dump"])

    def test_get_ubootenv(self):
        """ Test get_ubootenv command """
        self.fabric.get_ubootenv()
        for node in self.nodes:
            self.assertEqual(node.executed, ["get_ubootenv"])

    def test_ipmitool_command(self):
        """ Test ipmitool_command command """
        ipmitool_args = "power status"
        self.fabric.ipmitool_command(ipmitool_args)
        for node in self.nodes:
            self.assertEqual(node.executed, [("ipmitool_command", ipmitool_args)])


class DummyNode:
    """ Dummy node for the nodemanager tests """
    def __init__(self, ip_address, username="admin", password="admin",
            tftp=None, *args, **kwargs):
        self.executed = []
        self.ip_address = ip_address
        self.tftp = tftp

    def get_mac_addresses(self):
        self.executed.append("get_mac_addresses")
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

    def get_firmware_info(self):
        self.executed.append("get_firmware_info")

    def is_updatable(self, package, partition_arg="INACTIVE", priority=None):
        self.executed.append(("is_updatable", package))

    def update_firmware(self, package, partition_arg="INACTIVE",
            priority=None):
        self.executed.append(("update_firmware", package))
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

    def config_reset(self):
        self.executed.append("config_reset")

    def set_boot_order(self, boot_args):
        self.executed.append(("set_boot_order", boot_args))

    def get_boot_order(self):
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

    def info_dump(self):
        self.executed.append("info_dump")

    def ipmitool_command(self, ipmitool_args):
        self.executed.append(("ipmitool_command", ipmitool_args))
        return "Dummy output"

    def get_ubootenv(self):
        self.executed.append("get_ubootenv")

        ubootenv = UbootEnv()
        ubootenv.variables["bootcmd0"] = "run bootcmd_default"
        ubootenv.variables["bootcmd_default"] = "run bootcmd_sata"
        return ubootenv

    def get_fabric_ipinfo(self):
        return {}

class DummyImage:
    def __init__(self, filename, image_type, *args):
        self.filename = filename
        self.type = image_type


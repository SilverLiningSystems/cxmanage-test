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
"""Unit tests for the Node class."""


import random
import shutil
import tempfile
import unittest

from pyipmi import IpmiError
from pyipmi.bmc import LanBMC

from cxmanage_test import TestImage, TestSensor, random_file
from cxmanage_api.simg import create_simg
from cxmanage_api.node import Node
from cxmanage_api.tftp import InternalTftp, ExternalTftp
from cxmanage_api.ubootenv import UbootEnv
from cxmanage_api.firmware_package import FirmwarePackage
from cxmanage_api.cx_exceptions import IPDiscoveryError


NUM_NODES = 4
ADDRESSES = ["192.168.100.%i" % x for x in range(1, NUM_NODES+1)]

class NodeTest(unittest.TestCase):
    """ Tests involving cxmanage Nodes """

    def setUp(self):
        tftp = InternalTftp()
        self.nodes = [Node(ip_address=ip, tftp=tftp, bmc=DummyBMC,
                image=TestImage, ubootenv=DummyUbootEnv,
                ipretriever=DummyIPRetriever, verbose=True)
                for ip in ADDRESSES]

        # Set up an internal server
        self.work_dir = tempfile.mkdtemp(prefix="cxmanage_node_test-")

    def tearDown(self):
        shutil.rmtree(self.work_dir, ignore_errors=True)

    def test_get_power(self):
        """ Test node.get_power method """
        for node in self.nodes:
            result = node.get_power()

            self.assertEqual(node.bmc.executed, ["get_chassis_status"])
            self.assertEqual(result, False)

    def test_set_power(self):
        """ Test node.set_power method """
        for node in self.nodes:
            modes = ["off", "on", "reset", "off"]
            for mode in modes:
                node.set_power(mode)

            self.assertEqual(node.bmc.executed,
                    [("set_chassis_power", x) for x in modes])

    def test_get_power_policy(self):
        """ Test node.get_power_policy method """
        for node in self.nodes:
            result = node.get_power_policy()

            self.assertEqual(node.bmc.executed, ["get_chassis_status"])
            self.assertEqual(result, "always-off")

    def test_set_power_policy(self):
        """ Test node.set_power_policy method """
        for node in self.nodes:
            modes = ["always-on", "previous", "always-off"]
            for mode in modes:
                node.set_power_policy(mode)

            self.assertEqual(node.bmc.executed,
                    [("set_chassis_policy", x) for x in modes])

    def test_get_sensors(self):
        """ Test node.get_sensors method """
        for node in self.nodes:
            result = node.get_sensors()

            self.assertEqual(node.bmc.executed, ["sdr_list"])

            self.assertEqual(len(result), 2)
            self.assertTrue(result["Node Power"].sensor_reading.endswith("Watts"))
            self.assertTrue(result["Board Temp"].sensor_reading.endswith("degrees C"))

    def test_is_updatable(self):
        """ Test node.is_updatable method """
        for node in self.nodes:
            max_size = 12288 - 60
            filename = random_file(max_size)
            images = [
                TestImage(filename, "SOC_ELF"),
                TestImage(filename, "CDB"),
                TestImage(filename, "UBOOTENV")
            ]

            # should pass
            package = FirmwarePackage()
            package.images = images
            self.assertTrue(node.is_updatable(package))

            # should fail if the firmware version is wrong
            package = FirmwarePackage()
            package.images = images
            package.version = "ECX-31415-v0.0.0"
            self.assertFalse(node.is_updatable(package))

            # should fail if we specify a socman version
            package = FirmwarePackage()
            package.images = images
            package.required_socman_version = "0.0.1"
            self.assertFalse(node.is_updatable(package))

            # should fail if we try to upload a slot2
            package = FirmwarePackage()
            package.images = images
            package.config = "slot2"
            self.assertFalse(node.is_updatable(package))

            # should fail if we upload an image that's too large
            package = FirmwarePackage()
            package.images = [TestImage(random_file(max_size + 1), "UBOOTENV")]
            self.assertFalse(node.is_updatable(package))

            # should fail if we upload to a CDB partition that's in use
            package = FirmwarePackage()
            package.images = images
            self.assertFalse(node.is_updatable(package, partition_arg="ACTIVE"))

    def test_update_firmware(self):
        """ Test node.update_firmware method """
        filename = "%s/%s" % (self.work_dir, "image.bin")
        open(filename, "w").write("")

        package = FirmwarePackage()
        package.images = [
            TestImage(filename, "SOC_ELF"),
            TestImage(filename, "CDB"),
            TestImage(filename, "UBOOTENV")
        ]
        package.version = "0.0.1"

        for node in self.nodes:
            node.update_firmware(package)

            partitions = node.bmc.partitions
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

            self.assertEqual(node.bmc.executed[-1],
                    ("set_firmware_version", "0.0.1"))

    def test_config_reset(self):
        """ Test node.config_reset method """
        for node in self.nodes:
            node.config_reset()

            # Assert config reset
            executed = node.bmc.executed
            self.assertEqual(
                    len([x for x in executed if x == "reset_firmware"]), 1)

            # Assert sel clear
            self.assertEqual(
                    len([x for x in executed if x == "sel_clear"]), 1)

            # Assert ubootenv changes
            active = node.bmc.partitions[5]
            inactive = node.bmc.partitions[6]
            self.assertEqual(active.updates, 1)
            self.assertEqual(active.retrieves, 0)
            self.assertEqual(active.checks, 1)
            self.assertEqual(active.activates, 1)
            self.assertEqual(inactive.updates, 0)
            self.assertEqual(inactive.retrieves, 1)
            self.assertEqual(inactive.checks, 0)
            self.assertEqual(inactive.activates, 0)

    def test_set_boot_order(self):
        """ Test node.set_boot_order method """
        boot_args = ["disk", "pxe", "retry"]
        for node in self.nodes:
            node.set_boot_order(boot_args)

            partitions = node.bmc.partitions
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
        """ Test node.get_boot_order method """
        for node in self.nodes:
            result = node.get_boot_order()

            partitions = node.bmc.partitions
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

    def test_get_versions(self):
        """ Test node.get_versions method """
        for node in self.nodes:
            result = node.get_versions()

            self.assertEqual(node.bmc.executed, ["get_info_basic",
                    "get_firmware_info", "info_card"])
            for attr in ["iana", "firmware_version", "ecme_version",
                    "ecme_timestamp"]:
                self.assertTrue(hasattr(result, attr))

    def test_get_fabric_ipinfo(self):
        """ Test node.get_fabric_ipinfo method """
        for node in self.nodes:
            result = node.get_fabric_ipinfo()

            for x in node.bmc.executed:
                self.assertEqual(x, "get_fabric_ipinfo")
            self.assertEqual(result, dict([(i, ADDRESSES[i])
                    for i in range(NUM_NODES)]))

    def test_get_fabric_macaddrs(self):
        """ Test node.get_fabric_macaddrs method """
        for node in self.nodes:
            result = node.get_fabric_macaddrs()

            for x in node.bmc.executed:
                self.assertEqual(x, "get_fabric_macaddresses")
            self.assertEqual(len(result), NUM_NODES)
            for node_id in xrange(NUM_NODES):
                self.assertEqual(len(result[node_id]), 3)
                for port in result[node_id]:
                    expected_macaddr = "00:00:00:00:%x:%x" % (node_id, port)
                    self.assertEqual(result[node_id][port], [expected_macaddr])

    def test_get_server_ip(self):
        """ Test node.get_server_ip method """
        for node in self.nodes:
            result = node.get_server_ip()
            self.assertEqual(result, "192.168.200.1")


class DummyBMC(LanBMC):
    """ Dummy BMC for the node tests """
    def __init__(self, **kwargs):
        super(DummyBMC, self).__init__(**kwargs)
        self.executed = []
        self.partitions = [
                Partition(0, 3, 0, 393216, in_use=True),        # socman
                Partition(1, 10, 393216, 196608, in_use=True),  # factory cdb
                Partition(2, 3, 589824, 393216, in_use=False),  # socman
                Partition(3, 10, 983040, 196608, in_use=False), # factory cdb
                Partition(4, 10, 1179648, 196608, in_use=True), # running cdb
                Partition(5, 11, 1376256, 12288),               # ubootenv
                Partition(6, 11, 1388544, 12288)                # ubootenv
        ]

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

    def update_firmware(self, filename, partition, image_type, tftp_addr):
        """ Download a file from a TFTP server to a given partition.

        Make sure the image type matches. """
        self.executed.append(("update_firmware", filename,
                partition, image_type, tftp_addr))
        self.partitions[partition].updates += 1

        class Result:
            def __init__(self):
                self.tftp_handle_id = 0
        return Result()

    def retrieve_firmware(self, filename, partition, image_type, tftp_addr):
        self.executed.append(("retrieve_firmware", filename,
                partition, image_type, tftp_addr))
        self.partitions[partition].retrieves += 1

        # Upload blank image to tftp
        work_dir = tempfile.mkdtemp(prefix="cxmanage_test-")
        open("%s/%s" % (work_dir, filename), "w").write(create_simg(""))
        address, port = tftp_addr.split(":")
        port = int(port)
        tftp = ExternalTftp(address, port)
        tftp.put_file("%s/%s" % (work_dir, filename), filename)
        shutil.rmtree(work_dir)

        class Result:
            def __init__(self):
                self.tftp_handle_id = 0
        return Result()

    def register_firmware_read(self, filename, partition, image_type):
        self.executed.append(("register_firmware_read", filename, partition,
                image_type))
        raise IpmiError()

    def register_firmware_write(self, filename, partition, image_type):
        self.executed.append(("register_firmware_write", filename, partition,
                image_type))
        raise IpmiError()

    def get_firmware_status(self, handle):
        self.executed.append("get_firmware_status")

        class Result:
            def __init__(self):
                self.status = "Complete"
        return Result()

    def check_firmware(self, partition):
        self.executed.append(("check_firmware", partition))
        self.partitions[partition].checks += 1

        class Result:
            def __init__(self):
                self.crc32 = 0
                self.error = None
        return Result()

    def activate_firmware(self, partition):
        self.executed.append(("activate_firmware", partition))
        self.partitions[partition].activates += 1

    def set_firmware_version(self, version):
        self.executed.append(("set_firmware_version", version))

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
        self.executed.append("get_info_basic")

        class Result:
            def __init__(self):
                self.iana = int("0x0096CD", 16)
                self.firmware_version = "ECX-0000-v0.0.0"
                self.ecme_version = "v0.0.0"
                self.ecme_timestamp = 0
        return Result()

    def get_info_card(self):
        self.executed.append("info_card")

        class Result:
            def __init__(self):
                self.type = "TestBoard"
                self.revision = "0"
        return Result()

    def get_fabric_ipinfo(self, filename, tftp_address=None):
        """ Upload an ipinfo file from the node to TFTP"""
        self.executed.append("get_fabric_ipinfo")

        if tftp_address == None:
            raise IpmiError()

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

    def get_fabric_macaddresses(self, filename, tftp_address=None):
        """ Upload a macaddrs file from the node to TFTP"""
        self.executed.append("get_fabric_macaddresses")

        if tftp_address == None:
            raise IpmiError()

        work_dir = tempfile.mkdtemp(prefix="cxmanage_test-")

        # Create macaddrs file
        macaddrs = open("%s/%s" % (work_dir, filename), "w")
        for i in range(len(ADDRESSES)):
            for port in range(3):
                macaddr = "00:00:00:00:%x:%x" % (i, port)
                macaddrs.write("Node %i, Port %i: %s\n" % (i, port, macaddr))
        macaddrs.close()

        # Upload to tftp
        address, port = tftp_address.split(":")
        port = int(port)
        tftp = ExternalTftp(address, port)
        tftp.put_file("%s/%s" % (work_dir, filename), filename)

        shutil.rmtree(work_dir)


class Partition:
    def __init__(self, partition, type, offset=0,
            size=0, priority=0, daddr=0, in_use=None):
        self.updates = 0
        self.retrieves = 0
        self.checks = 0
        self.activates = 0
        self.fwinfo = FWInfoEntry(partition, type, offset, size, priority,
                                  daddr, in_use)


class FWInfoEntry:
    """ Firmware info for a single partition """

    def __init__(self, partition, type, offset=0, size=0, priority=0, daddr=0,
                  in_use=None):
        self.partition = "%2i" % partition
        self.type = {
                2: "02 (S2_ELF)",
                3: "03 (SOC_ELF)",
                10: "0a (CDB)",
                11: "0b (UBOOTENV)"
            }[type]
        self.offset = "%8x" % offset
        self.size = "%8x" % size
        self.priority = "%8x" % priority
        self.daddr = "%8x" % daddr
        self.in_use = {None: "Unknown", True: "1", False: "0"}[in_use]
        self.flags = "fffffffd"
        self.version = "v0.0.0"


class DummyUbootEnv(UbootEnv):
    """UbootEnv info."""

    def get_boot_order(self):
        """Hard coded boot order for testing."""
        return ["disk", "pxe"]


class DummyIPRetriever(object):
    """ Dummy IP retriever """

    def __init__(self, ecme_ip, aggressive=False, verbosity=0, **kwargs):
        self.executed = False
        self.ecme_ip = ecme_ip
        self.aggressive = aggressive
        self.verbosity = verbosity
        for name, value in kwargs.iteritems():
            setattr(self, name, value)

    def run(self):
        """ Set the server_ip variable. Raises an error if called more than
        once. """
        if self.executed:
            raise IPDiscoveryError("DummyIPRetriever.run() was called twice!")
        self.executed = True
        self.server_ip = "192.168.200.1"

# End of file: node_test.py

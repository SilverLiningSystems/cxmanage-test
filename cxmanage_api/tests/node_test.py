# pylint: disable=too-many-public-methods

# Copyright (c) 2012-2013, Calxeda Inc.
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

import shutil
import tempfile
import unittest
from mock import call

from cxmanage_api.tests import DummyBMC, DummyUbootEnv, DummyIPRetriever
from cxmanage_api.tests import TestImage, random_file
from cxmanage_api.node import Node
from cxmanage_api.firmware_package import FirmwarePackage


class NodeTest(unittest.TestCase):
    """ Tests involving cxmanage Nodes """

    def setUp(self):
        self.nodes = [
            Node(
                ip_address=ip, tftp=DummyBMC.tftp, bmc=DummyBMC,
                image=TestImage, ubootenv=DummyUbootEnv,
                ipretriever=DummyIPRetriever, verbose=True
            ) for ip in DummyBMC.ip_addresses
        ]

        # Give each node a node_id
        count = 0
        for node in self.nodes:
            node.node_id = count
            count = count + 1

        # Set up an internal server
        self.work_dir = tempfile.mkdtemp(prefix="cxmanage_node_test-")

    def tearDown(self):
        shutil.rmtree(self.work_dir, ignore_errors=True)

    def test_get_power(self):
        """ Test node.get_power method """
        for node in self.nodes:
            result = node.get_power()

            self.assertEqual(node.bmc.method_calls, [call.get_chassis_status()])
            self.assertEqual(result, False)

    def test_set_power(self):
        """ Test node.set_power method """
        for node in self.nodes:
            modes = ["off", "on", "reset", "off"]
            for mode in modes:
                node.set_power(mode)

            self.assertEqual(
                node.bmc.method_calls,
                [call.set_chassis_power(mode=x) for x in modes]
            )

    def test_get_power_policy(self):
        """ Test node.get_power_policy method """
        for node in self.nodes:
            result = node.get_power_policy()

            self.assertEqual(node.bmc.method_calls, [call.get_chassis_status()])
            self.assertEqual(result, "always-off")

    def test_set_power_policy(self):
        """ Test node.set_power_policy method """
        for node in self.nodes:
            modes = ["always-on", "previous", "always-off"]
            for mode in modes:
                node.set_power_policy(mode)

            self.assertEqual(
                node.bmc.method_calls,
                [call.set_chassis_policy(x) for x in modes]
            )

    def test_get_sensors(self):
        """ Test node.get_sensors method """
        for node in self.nodes:
            result = node.get_sensors()

            self.assertEqual(node.bmc.method_calls, [call.sdr_list()])

            self.assertEqual(len(result), 2)
            self.assertTrue(
                result["Node Power"].sensor_reading.endswith("Watts")
            )
            self.assertTrue(
                result["Board Temp"].sensor_reading.endswith("degrees C")
            )

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
                self.assertEqual(partition.checks, 2)
                self.assertEqual(partition.activates, 1)

            self.assertEqual(ubootenv_partition.updates, 1)
            self.assertEqual(ubootenv_partition.retrieves, 1)
            self.assertEqual(ubootenv_partition.checks, 2)
            self.assertEqual(ubootenv_partition.activates, 1)

            node.bmc.set_firmware_version.assert_called_once_with("0.0.1")

    def test_config_reset(self):
        """ Test node.config_reset method """
        for node in self.nodes:
            node.config_reset()

            # Assert config reset
            self.assertEqual(node.bmc.reset_firmware.call_count, 1)

            # Assert sel clear
            self.assertEqual(node.bmc.sel_clear.call_count, 1)

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

    def test_set_pxe_interface(self):
        """ Test node.set_pxe_interface method """
        for node in self.nodes:
            node.set_pxe_interface("eth0")

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

    def test_get_pxe_interface(self):
        """ Test node.get_pxe_interface method """
        for node in self.nodes:
            result = node.get_pxe_interface()

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

            self.assertEqual(result, "eth0")

    def test_get_versions(self):
        """ Test node.get_versions method """
        for node in self.nodes:
            result = node.get_versions()

            self.assertEqual(node.bmc.method_calls, [
                call.get_info_basic(),
                call.get_firmware_info(),
                call.get_info_card(),
                call.pmic_get_version()
            ])
            for attr in ["iana", "firmware_version", "ecme_version",
                    "ecme_timestamp"]:
                self.assertTrue(hasattr(result, attr))

    def test_get_fabric_ipinfo(self):
        """ Test node.get_fabric_ipinfo method """
        for node in self.nodes:
            result = node.get_fabric_ipinfo()

            self.assertTrue(node.bmc.fabric_config_get_ip_info.called)

            self.assertEqual(result, dict([(i, DummyBMC.ip_addresses[i])
                    for i in range(len(DummyBMC.ip_addresses))]))

    def test_get_fabric_macaddrs(self):
        """ Test node.get_fabric_macaddrs method """
        for node in self.nodes:
            result = node.get_fabric_macaddrs()

            self.assertTrue(node.bmc.fabric_config_get_mac_addresses.called)

            self.assertEqual(len(result), len(DummyBMC.ip_addresses))
            for node_id in xrange(len(DummyBMC.ip_addresses)):
                self.assertEqual(len(result[node_id]), 3)
                for port in result[node_id]:
                    expected_macaddr = "00:00:00:00:%x:%x" % (node_id, port)
                    self.assertEqual(result[node_id][port], [expected_macaddr])

    def test_get_fabric_uplink_info(self):
        """ Test node.get_fabric_uplink_info method """
        for node in self.nodes:
            node.get_fabric_uplink_info()
            self.assertTrue(node.bmc.fabric_config_get_uplink_info.called)

    def test_get_uplink_info(self):
        """ Test node.get_uplink_info method """
        for node in self.nodes:
            node.get_uplink_info()
            self.assertTrue(node.bmc.fabric_get_uplink_info.called)

    def test_get_uplink_speed(self):
        """ Test node.get_uplink_info method """
        for node in self.nodes:
            node.get_uplink_speed()
            self.assertTrue(node.bmc.fabric_get_uplink_speed.called)

    def test_get_linkmap(self):
        """ Test node.get_linkmap method """
        for node in self.nodes:
            node.get_linkmap()
            self.assertTrue(node.bmc.fabric_info_get_link_map.called)

    def test_get_routing_table(self):
        """ Test node.get_routing_table method """
        for node in self.nodes:
            node.get_routing_table()
            self.assertTrue(node.bmc.fabric_info_get_routing_table.called)

    def test_get_depth_chart(self):
        """ Test node.get_depth_chart method """
        for node in self.nodes:
            node.get_depth_chart()
            self.assertTrue(node.bmc.fabric_info_get_depth_chart.called)

    def test_get_link_stats(self):
        """ Test node.get_link_stats() """
        for node in self.nodes:
            node.get_link_stats()
            self.assertTrue(node.bmc.fabric_get_linkstats.called)

    def test_get_server_ip(self):
        """ Test node.get_server_ip method """
        for node in self.nodes:
            result = node.get_server_ip()
            self.assertEqual(result, "192.168.200.1")

    def test_get_linkspeed(self):
        """ Test node.get_linkspeed method """
        for node in self.nodes:
            result = node.get_linkspeed()
            self.assertEqual(result, 1)

    def test_get_uplink(self):
        """ Test node.get_uplink method"""
        for node in self.nodes:
            result = node.get_uplink(iface=0)
            self.assertEqual(result, 0)

    def test_set_uplink(self):
        """ Test node.set_uplink method """
        for node in self.nodes:
            node.set_uplink(iface=0, uplink=0)
            self.assertEqual(node.get_uplink(iface=0), 0)

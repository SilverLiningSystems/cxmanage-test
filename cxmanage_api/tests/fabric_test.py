# pylint: disable=protected-access
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

"""Calxeda: fabric_test.py """

import random
import unittest
from mock import call

from cxmanage_api.fabric import Fabric
from cxmanage_api.tftp import InternalTftp, ExternalTftp
from cxmanage_api.firmware_package import FirmwarePackage
from cxmanage_api.cx_exceptions import CommandFailedError
from cxmanage_api.tests import DummyNode, DummyFailNode


class FabricTest(unittest.TestCase):
    """ Test the various Fabric commands """
    def setUp(self):
        # Set up the controller and add targets
        self.fabric = Fabric(DummyNode.ip_addresses[0], node=DummyNode)
        self.nodes = [DummyNode(i) for i in DummyNode.ip_addresses]
        self.fabric._nodes = dict((i, self.nodes[i])
                for i in xrange(len(self.nodes)))

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

    def test_get_mac_addresses(self):
        """ Test get_mac_addresses command """
        self.fabric.get_mac_addresses()
        self.assertEqual(
            self.nodes[0].method_calls,
            [call.get_fabric_macaddrs()]
        )
        for node in self.nodes[1:]:
            self.assertEqual(node.method_calls, [])

    def test_get_uplink_info(self):
        """ Test get_uplink_info command """
        self.fabric.get_uplink_info()
        for node in self.nodes:
            self.assertEqual(node.method_calls, [call.get_uplink_info()])

    def test_get_uplink_speed(self):
        """ Test get_uplink_speed command """
        self.fabric.get_uplink_speed()
        for node in self.nodes:
            self.assertEqual(node.method_calls, [call.get_uplink_speed()])

    def test_get_uplink(self):
        """ Test get_uplink command """
        self.assertEqual(self.fabric.get_uplink(iface=0), 0)

    def test_set_uplink(self):
        """ Test set_uplink command """
        iface, uplink = 0, 0
        self.fabric.set_uplink(iface=iface, uplink=uplink)
        self.assertEqual(
            self.nodes[0].bmc.method_calls,
            [call.fabric_config_set_uplink(iface=iface, uplink=uplink)]
        )

    def test_get_sensors(self):
        """ Test get_sensors command """
        self.fabric.get_sensors()
        self.fabric.get_sensors("Node Power")
        for node in self.nodes:
            self.assertEqual(node.method_calls, [
                call.get_sensors(""), call.get_sensors("Node Power")
            ])

    def test_get_firmware_info(self):
        """ Test get_firmware_info command """
        self.fabric.get_firmware_info()
        for node in self.nodes:
            self.assertEqual(node.method_calls, [call.get_firmware_info()])

    def test_is_updatable(self):
        """ Test is_updatable command """
        package = FirmwarePackage()
        self.fabric.is_updatable(package)
        for node in self.nodes:
            self.assertEqual(node.method_calls, [
                call.is_updatable(package, "INACTIVE", None)
            ])

    def test_update_firmware(self):
        """ Test update_firmware command """
        package = FirmwarePackage()
        self.fabric.update_firmware(package)
        for node in self.nodes:
            self.assertEqual(node.method_calls, [
                call.update_firmware(package, "INACTIVE", None)
            ])

    def test_config_reset(self):
        """ Test config_reset command """
        self.fabric.config_reset()
        for node in self.nodes:
            self.assertEqual(node.method_calls, [call.config_reset()])

    def test_set_boot_order(self):
        """ Test set_boot_order command """
        boot_args = "disk0,pxe,retry"
        self.fabric.set_boot_order(boot_args)
        for node in self.nodes:
            self.assertEqual(
                node.method_calls, [call.set_boot_order(boot_args)]
            )

    def test_get_boot_order(self):
        """ Test get_boot_order command """
        self.fabric.get_boot_order()
        for node in self.nodes:
            self.assertEqual(node.method_calls, [call.get_boot_order()])

    def test_set_pxe_interface(self):
        """ Test set_pxe_interface command """
        self.fabric.set_pxe_interface("eth0")
        for node in self.nodes:
            self.assertEqual(
                node.method_calls, [call.set_pxe_interface("eth0")]
            )

    def test_get_pxe_interface(self):
        """ Test get_pxe_interface command """
        self.fabric.get_pxe_interface()
        for node in self.nodes:
            self.assertEqual(node.method_calls, [call.get_pxe_interface()])

    def test_get_versions(self):
        """ Test get_versions command """
        self.fabric.get_versions()
        for node in self.nodes:
            self.assertEqual(node.method_calls, [call.get_versions()])

    def test_get_ubootenv(self):
        """ Test get_ubootenv command """
        self.fabric.get_ubootenv()
        for node in self.nodes:
            self.assertEqual(node.method_calls, [call.get_ubootenv()])

    def test_ipmitool_command(self):
        """ Test ipmitool_command command """
        ipmitool_args = "power status"
        self.fabric.ipmitool_command(ipmitool_args)
        for node in self.nodes:
            self.assertEqual(
                node.method_calls, [call.ipmitool_command(ipmitool_args)]
            )

    def test_get_server_ip(self):
        """ Test get_server_ip command """
        self.fabric.get_server_ip("interface", "ipv6", "aggressive")
        for node in self.nodes:
            self.assertEqual(node.method_calls,
                [call.get_server_ip("interface", "ipv6", "aggressive")]
            )

    def test_failed_command(self):
        """ Test a failed command """
        fail_nodes = [DummyFailNode(i) for i in DummyNode.ip_addresses]
        self.fabric._nodes = dict(
            (i, fail_nodes[i]) for i in xrange(len(self.nodes))
        )
        try:
            self.fabric.get_power()
            self.fail()
        except CommandFailedError:
            for node in fail_nodes:
                self.assertEqual(node.method_calls, [call.get_power()])

    def test_primary_node(self):
        """Test the primary_node property

        Currently it should always return node 0.
        """
        self.assertEqual(self.fabric.primary_node, self.nodes[0])

    def test_get_ipsrc(self):
        """Test the get_ipsrc method

        """
        self.fabric.get_ipsrc()
        self.assertEqual(self.fabric.primary_node.bmc.method_calls, [
            call.fabric_config_get_ip_src()
        ])

    def test_set_ipsrc(self):
        """Test the set_ipsrc method"""

        ipsrc = random.randint(1, 2)

        self.fabric.set_ipsrc(ipsrc)
        self.assertEqual(self.fabric.primary_node.bmc.method_calls, [
            call.fabric_config_set_ip_src(ipsrc)
        ])

    def test_apply_fdc(self):
        """Test the apply_factory_default_config method"""

        self.fabric.apply_factory_default_config()
        self.assertEqual(self.fabric.primary_node.bmc.method_calls, [
            call.fabric_config_factory_default()
        ])

    def test_get_ipaddr_base(self):
        """Test the get_ipaddr_base method"""
        self.fabric.get_ipaddr_base()
        self.assertEqual(self.fabric.primary_node.bmc.method_calls, [
            call.fabric_config_get_ip_addr_base()
        ])

    def test_update_config(self):
        """Test the update_config method

        """
        self.fabric.update_config()
        self.assertEqual(self.fabric.primary_node.bmc.method_calls, [
            call.fabric_config_update_config()
        ])

    def test_get_linkspeed(self):
        """Test the get_linkspeed method

        """
        self.fabric.get_linkspeed()
        self.assertEqual(self.fabric.primary_node.bmc.method_calls, [
            call.fabric_config_get_linkspeed()
        ])

    def test_set_linkspeed(self):
        """Test the set_linkspeed method"""

        valid_linkspeeds = [1, 2.5, 5, 7.5, 10]
        linkspeed = random.choice(valid_linkspeeds)

        self.fabric.set_linkspeed(linkspeed)
        self.assertEqual(self.fabric.primary_node.bmc.method_calls, [
            call.fabric_config_set_linkspeed(linkspeed)
        ])

    def test_get_linkspeed_policy(self):
        """Test the get_linkspeed_policy method

        """
        self.fabric.get_linkspeed_policy()
        self.assertTrue(self.fabric.primary_node.bmc.method_calls, [
            call.fabric_config_get_linkspeed_policy()
        ])

    def test_set_linkspeed_policy(self):
        """Test the set_linkspeed_policy method"""

        ls_policy = random.randint(0, 1)

        self.fabric.set_linkspeed_policy(ls_policy)
        self.assertEqual(self.fabric.primary_node.bmc.method_calls, [
            call.fabric_config_set_linkspeed_policy(ls_policy)
        ])

    def test_get_link_stats(self):
        """Test the get_link_stats() method."""
        for i in range(0, 5):
            self.fabric.get_link_stats(i)
            for node in self.fabric.nodes.values():
                node.get_link_stats.assert_called_with(i)

    def test_get_linkmap(self):
        """Test the get_linkmap method"""
        self.fabric.get_linkmap()
        for node in self.fabric.nodes.values():
            self.assertTrue(node.get_linkmap.called)

    def test_get_routing_table(self):
        """Test the get_routing_table method"""
        self.fabric.get_routing_table()
        for node in self.fabric.nodes.values():
            self.assertTrue(node.get_routing_table.called)

    def test_get_depth_chart(self):
        """Test the depth_chart method"""
        self.fabric.get_depth_chart()
        for node in self.fabric.nodes.values():
            self.assertTrue(node.get_depth_chart.called)

    def test_get_link_users_factor(self):
        """Test the get_link_users_factor method

        """
        self.fabric.get_link_users_factor()
        self.assertEqual(self.fabric.primary_node.bmc.method_calls, [
            call.fabric_config_get_link_users_factor()
        ])

    def test_set_link_users_factor(self):
        """Test the set_link_users_factor method"""

        lu_factor = random.randint(5, 50)

        self.fabric.set_link_users_factor(lu_factor)
        self.assertEqual(self.fabric.primary_node.bmc.method_calls, [
            call.fabric_config_set_link_users_factor(lu_factor)
        ])

    def test_add_macaddr (self):
        """Test the add_macaddr method"""

        valid_nodeids = [0, 1, 2, 3]
        t_nodeid = random.choice(valid_nodeids)

        valid_ifaces = [0, 1, 2]
        t_iface = random.choice(valid_ifaces)

        t_macaddr = "66:55:44:33:22:11"

        self.fabric.add_macaddr (t_nodeid, t_iface, t_macaddr)
        self.assertTrue(self.fabric.primary_node.bmc.fabric_add_macaddr.called)

    def test_rm_macaddr (self):
        """Test the rm_macaddr method"""

        valid_nodeids = [0, 1, 2, 3]
        t_nodeid = random.choice(valid_nodeids)

        valid_ifaces = [0, 1, 2]
        t_iface = random.choice(valid_ifaces)

        t_macaddr = "66:55:44:33:22:11"

        self.fabric.rm_macaddr (t_nodeid, t_iface, t_macaddr)
        self.assertTrue(self.fabric.primary_node.bmc.fabric_rm_macaddr.called)

    def test_set_macaddr_base(self):
        """Test the set_macaddr_base method"""
        self.fabric.set_macaddr_base("00:11:22:33:44:55")
        for node in self.fabric.nodes.values():
            if node == self.fabric.primary_node:
                self.assertEqual(node.bmc.method_calls, [
                    call.fabric_config_set_macaddr_base(
                        macaddr="00:11:22:33:44:55"
                    )
                ])
            else:
                self.assertEqual(node.bmc.method_calls, [])

    def test_get_macaddr_base(self):
        """Test the get_macaddr_base method"""
        self.assertEqual(self.fabric.get_macaddr_base(), "00:00:00:00:00:00")
        for node in self.fabric.nodes.values():
            if node == self.fabric.primary_node:
                self.assertEqual(
                    node.bmc.method_calls,
                    [call.fabric_config_get_macaddr_base()]
                )
            else:
                self.assertEqual(node.bmc.method_calls, [])

    def test_set_macaddr_mask(self):
        """Test the set_macaddr_mask method"""
        self.fabric.set_macaddr_mask("00:11:22:33:44:55")
        for node in self.fabric.nodes.values():
            if node == self.fabric.primary_node:
                self.assertEqual(node.bmc.method_calls, [
                    call.fabric_config_set_macaddr_mask(
                        mask="00:11:22:33:44:55"
                    )
                ])
            else:
                self.assertEqual(node.bmc.method_calls, [])

    def test_get_macaddr_mask(self):
        """Test the get_macaddr_mask method"""
        self.assertEqual(self.fabric.get_macaddr_mask(), "00:00:00:00:00:00")
        for node in self.fabric.nodes.values():
            if node == self.fabric.primary_node:
                self.assertEqual(
                    node.bmc.method_calls,
                    [call.fabric_config_get_macaddr_mask()]
                )
            else:
                self.assertEqual(node.bmc.method_calls, [])

    def test_composite_bmc(self):
        """ Test the CompositeBMC member """
        with self.assertRaises(AttributeError):
            self.fabric.cbmc.fake_method()

        self.fabric.cbmc.set_chassis_power("off")
        results = self.fabric.cbmc.get_chassis_status()

        self.assertEqual(len(results), len(self.fabric.nodes))
        for node_id in self.fabric.nodes:
            self.assertFalse(results[node_id].power_on)

        for node in self.fabric.nodes.values():
            self.assertEqual(node.bmc.method_calls, [
                call.set_chassis_power("off"),
                call.get_chassis_status()
            ])



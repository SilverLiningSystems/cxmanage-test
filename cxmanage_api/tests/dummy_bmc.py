# pylint: disable=invalid-name
# pylint: disable=no-self-use
# pylint: disable=too-few-public-methods
# pylint: disable=too-many-arguments
# pylint: disable=too-many-instance-attributes
# pylint: disable=too-many-public-methods
# pylint: disable=unused-argument

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

""" Module for the DummyBMC class """

import random
import shutil
import tempfile
from mock import Mock

from pyipmi import IpmiError
from pyipmi.bmc import LanBMC

from cxmanage_api.tests import Dummy, TestSensor
from cxmanage_api import temp_file
from cxmanage_api.simg import create_simg, get_simg_header
from cxmanage_api.tftp import InternalTftp, ExternalTftp


class DummyBMC(Dummy):
    """ Dummy BMC for the node tests """
    dummy_spec = LanBMC

    ip_addresses = [
        "192.168.100.%i" % n for n in range(1, 5)
    ]
    tftp = InternalTftp()


    GUID_UNIQUE = 0


    def __init__(self, **kwargs):
        super(DummyBMC, self).__init__()
        self.handle = Mock(name="handle")
        self.partitions = [
                Partition(0, 3, 0, 393216, in_use=True),  # socman
                Partition(1, 10, 393216, 196608, in_use=True),  # factory cdb
                Partition(2, 3, 589824, 393216, in_use=False),  # socman
                Partition(3, 10, 983040, 196608, in_use=False),  # factory cdb
                Partition(4, 10, 1179648, 196608, in_use=True),  # running cdb
                Partition(5, 11, 1376256, 12288),  # ubootenv
                Partition(6, 11, 1388544, 12288)  # ubootenv
        ]
        self.ipaddr_base = '192.168.100.1'
        self.unique_guid = 'FAKEGUID%s' % DummyBMC.GUID_UNIQUE
        self.sel = DummyBMC.generate_sel(with_errors=False)

        DummyBMC.GUID_UNIQUE += 1

    def guid(self):
        """Returns the GUID"""
        return Result(system_guid=self.unique_guid, time_stamp=None)

    def get_chassis_status(self):
        """ Get chassis status """
        return Result(power_on=False, power_restore_policy="always-off")

    def sel_elist(self):
        """ List SEL. with_errors=True simulates a SEL that contains errors """
        return self.sel

    @staticmethod
    def generate_sel(with_errors=False):
        """ Generates a SEL table for a Node """
        if (with_errors):
            return [
            '1 | 11/20/2013 | 20:26:18 | Memory | Correctable ECC | Asserted',
            '2 | 11/20/2013 | 20:26:43 | Processor | IERR | Asserted',
            '83 | 11/14/2013 | 18:01:35 | OS Stop/Shutdown OS Stop Reason | ' +
            'Error during system startup | Asserted'
        ]
        else:
            return [
                '88 | 11/14/2013 | 18:02:29 | System Boot Initiated OS Boot ' +
                'Reason | Initiated by power up | Asserted',
                '91 | 11/14/2013 | 19:24:25 | System Event BMC Status |',
            ]

    def get_firmware_info(self):
        """ Get partition and simg info """
        return [x.fwinfo for x in self.partitions]

    def update_firmware(self, filename, partition, image_type, tftp_addr):
        """ Download a file from a TFTP server to a given partition.

        Make sure the image type matches. """
        self.partitions[partition].updates += 1

        localfile = temp_file()
        self.tftp.get_file(filename, localfile)

        contents = open(localfile).read()
        simg = get_simg_header(contents)
        self.partitions[partition].fwinfo.offset = "%8x" % simg.imgoff
        self.partitions[partition].fwinfo.size = "%8x" % simg.imglen
        self.partitions[partition].fwinfo.priority = "%8x" % simg.priority
        self.partitions[partition].fwinfo.daddr = "%8x" % simg.daddr

        return Result(tftp_handle_id = 0)

    def retrieve_firmware(self, filename, partition, image_type, tftp_addr):
        """ Mock retrieve_firmware method """
        self.partitions[partition].retrieves += 1

        # Upload blank image to tftp
        work_dir = tempfile.mkdtemp(prefix="cxmanage_test-")
        open("%s/%s" % (work_dir, filename), "w").write(create_simg(""))
        address, port = tftp_addr.split(":")
        port = int(port)
        tftp = ExternalTftp(address, port)
        tftp.put_file("%s/%s" % (work_dir, filename), filename)
        shutil.rmtree(work_dir)

        return Result(tftp_handle_id = 0)

    def register_firmware_read(self, filename, partition, image_type):
        """ Mock register_firmware_read method. currently not supported """
        raise IpmiError()

    def register_firmware_write(self, filename, partition, image_type):
        """ Mock register_firmware_write method. currently not supported """
        raise IpmiError()

    def get_firmware_status(self, handle):
        """ Mock get_firmware_status method """
        return Result(status="Complete")

    def check_firmware(self, partition):
        """ Mock check_firmware method """
        self.partitions[partition].checks += 1

        return Result(crc32=0, error=None)

    def activate_firmware(self, partition):
        """ Mock activate_firmware method """
        self.partitions[partition].activates += 1

    def sdr_list(self):
        """ Get sensor info from the node. """
        power_value = "%f (+/- 0) Watts" % random.uniform(0, 10)
        temp_value = "%f (+/- 0) degrees C" % random.uniform(30, 50)
        sensors = [
                TestSensor("Node Power", power_value),
                TestSensor("Board Temp", temp_value)
        ]

        return sensors

    def get_info_basic(self):
        """ Get basic SoC info from this node """
        return Result(
            iana=int("0x0096CD", 16),
            firmware_version="ECX-0000-v0.0.0",
            ecme_version="v0.0.0",
            ecme_timestamp=0
        )

    def get_info_card(self):
        """ Mock get_info_card method """
        return Result(type="TestBoard", revision="0")

    node_count = 0
    def fabric_get_node_id(self):
        """ Mock fabric_get_node_id method """
        result = DummyBMC.node_count
        DummyBMC.node_count += 1
        return result

    def fabric_info_get_link_map(self, filename, tftp_addr=None):
        """Upload a link_map file from the node to TFTP"""
        if not(tftp_addr):
            raise IpmiError('No tftp address!')

        link_map = []
        link_map.append('Link 1: Node 2')
        link_map.append('Link 3: Node 1')
        link_map.append('Link 4: Node 3')

        work_dir = tempfile.mkdtemp(prefix="cxmanage_test-")
        with open('%s/%s' % (work_dir, filename), 'w') as lm_file:
            for lmap in link_map:
                lm_file.write(lmap + '\n')
            lm_file.close()

        # Upload to tftp
        address, port = tftp_addr.split(":")
        port = int(port)
        tftp = ExternalTftp(address, port)
        tftp.put_file("%s/%s" % (work_dir, filename), filename)

        shutil.rmtree(work_dir)

    def fabric_info_get_routing_table(self, filename, tftp_addr=None):
        """Upload a routing_table file from the node to TFTP"""
        if not(tftp_addr):
            raise IpmiError('No tftp address!')

        routing_table = []
        routing_table.append('Node 1: rt - 0.2.0.3.2')
        routing_table.append('Node 2: rt - 0.3.0.1.2')
        routing_table.append('Node 3: rt - 0.2.0.1.3')
        routing_table.append('Node 12: rt - 0.2.0.0.1')
        routing_table.append('Node 13: rt - 0.2.0.0.1')
        routing_table.append('Node 14: rt - 0.2.0.0.1')
        routing_table.append('Node 15: rt - 0.2.0.0.1')

        work_dir = tempfile.mkdtemp(prefix="cxmanage_test-")
        with open('%s/%s' % (work_dir, filename), 'w') as rt_file:
            for rtable in routing_table:
                rt_file.write(rtable + '\n')
            rt_file.close()

        # Upload to tftp
        address, port = tftp_addr.split(":")
        port = int(port)
        tftp = ExternalTftp(address, port)
        tftp.put_file("%s/%s" % (work_dir, filename), filename)

        shutil.rmtree(work_dir)

    def fabric_info_get_depth_chart(self, filename, tftp_addr=None):
        """Upload a depth_chart file from the node to TFTP"""
        if not(tftp_addr):
            raise IpmiError('No tftp address!')

        depth_chart = []
        depth_chart.append(
           'Node 1: Shortest Distance 0 hops via neighbor 0: ' +
           'other hops/neighbors -'
        )
        depth_chart.append(
            'Node 2: Shortest Distance 0 hops via neighbor 0: ' +
            'other hops/neighbors - 1/3'
        )
        depth_chart.append(
            'Node 3: Shortest Distance 0 hops via neighbor 0: ' +
            'other hops/neighbors - 1/2'
        )
        depth_chart.append(
            'Node 4: Shortest Distance 2 hops via neighbor 6: ' +
            'other hops/neighbors - 3/7'
        )
        depth_chart.append(
            'Node 5: Shortest Distance 3 hops via neighbor 4: ' +
            'other hops/neighbors -'
        )
        depth_chart.append(
            'Node 6: Shortest Distance 1 hops via neighbor 2: ' +
            'other hops/neighbors -'
        )
        depth_chart.append(
            'Node 7: Shortest Distance 2 hops via neighbor 6: ' +
            'other hops/neighbors - 3/4'
        )
        depth_chart.append(
            'Node 8: Shortest Distance 3 hops via neighbor 10: ' +
            'other hops/neighbors - 4/11'
        )
        depth_chart.append(
            'Node 9: Shortest Distance 4 hops via neighbor 8: ' +
            'other hops/neighbors -'
        )
        depth_chart.append(
            'Node 10: Shortest Distance 2 hops via neighbor 6: ' +
            'other hops/neighbors -'
        )
        depth_chart.append(
            'Node 11: Shortest Distance 3 hops via neighbor 10: ' +
            'other hops/neighbors - 4/8'
        )
        depth_chart.append(
            'Node 12: Shortest Distance 4 hops via neighbor 14: ' +
            'other hops/neighbors - 5/15'
        )
        depth_chart.append(
            'Node 13: Shortest Distance 5 hops via neighbor 12: ' +
            'other hops/neighbors -'
        )
        depth_chart.append(
            'Node 14: Shortest Distance 3 hops via neighbor 10: ' +
            'other hops/neighbors -'
        )
        depth_chart.append(
            'Node 15: Shortest Distance 4 hops via neighbor 14: ' +
            'other hops/neighbors - 5/12'
        )

        work_dir = tempfile.mkdtemp(prefix="cxmanage_test-")
        with open('%s/%s' % (work_dir, filename), 'w') as dc_file:
            for dchart in depth_chart:
                dc_file.write(dchart + '\n')
            dc_file.close()

        # Upload to tftp
        address, port = tftp_addr.split(":")
        port = int(port)
        tftp = ExternalTftp(address, port)
        tftp.put_file("%s/%s" % (work_dir, filename), filename)

        shutil.rmtree(work_dir)

    def fabric_get_linkstats(self, filename, tftp_addr=None,
                             link=None):
        """Upload a link_stats file from the node to TFTP"""
        if not(tftp_addr):
            raise IpmiError('No tftp address!')

        link_stats = []
        link_stats.append('Packet Counts for Link %s:' % link)
        link_stats.append('Link0 StatspFS_LCn_CFG_0(link) = 0x1030d07f')
        link_stats.append('pFS_LCn_CFG_1 = 0x105f')
        link_stats.append('pFS_LCn_STATE = 0x1033')
        link_stats.append('pFS_LCn_SC_STAT = 0x0')
        link_stats.append('pFS_LCn_PKT_CNT_0 = 0x0')
        link_stats.append('pFS_LCn_PKT_CNT_1 = 0x0')
        link_stats.append('pFS_LCn_BYTE_CNT_0 = 0x0')
        link_stats.append('pFS_LCn_BYTE_CNT_1 = 0x0')
        link_stats.append('pFS_LCn_CM_TXDATA_0 = 0x82000000')
        link_stats.append('pFS_LCn_CM_TXDATA_1 = 0x0')
        link_stats.append('pFS_LCn_CM_RXDATA_0 = 0x0')
        link_stats.append('pFS_LCn_CM_RXDATA_1 = 0x0')
        link_stats.append('pFS_LCn_PKT_CNT_0 = 0x0')
        link_stats.append('pFS_LCn_PKT_CNT_1 = 0x0')
        link_stats.append('pFS_LCn_RMCSCNT = 0x1428')
        link_stats.append('pFS_LCn_RUCSCNT = 0x116')
        link_stats.append('pFS_LCn_RERRSCNT = 0x0')
        link_stats.append('pFS_LCn_RDRPSCNT = 0xb4')
        link_stats.append('pFS_LCn_RPKTSCNT = 0x0')
        link_stats.append('pFS_LCn_TPKTSCNT = 0x1')
        link_stats.append('pFS_LCn_TDRPSCNT = 0x0')

        work_dir = tempfile.mkdtemp(prefix="cxmanage_test-")
        with open('%s/%s' % (work_dir, filename), 'w') as ls_file:
            for stat in link_stats:
                ls_file.write(stat + '\n')
            ls_file.close()

        # Upload to tftp
        address, port = tftp_addr.split(":")
        port = int(port)
        tftp = ExternalTftp(address, port)
        tftp.put_file("%s/%s" % (work_dir, filename), filename)

        shutil.rmtree(work_dir)

    def fabric_config_get_ip_info(self, filename, tftp_addr=None):
        """ Upload an ipinfo file from the node to TFTP"""
        if not(tftp_addr):
            raise IpmiError('No tftp address!')

        work_dir = tempfile.mkdtemp(prefix="cxmanage_test-")

        # Create IP info file
        ipinfo = open("%s/%s" % (work_dir, filename), "w")
        for i in range(len(self.ip_addresses)):
            ipinfo.write("Node %i: %s\n" % (i, self.ip_addresses[i]))
        ipinfo.close()

        # Upload to tftp
        address, port = tftp_addr.split(":")
        port = int(port)
        tftp = ExternalTftp(address, port)
        tftp.put_file("%s/%s" % (work_dir, filename), filename)

        shutil.rmtree(work_dir)

    def fabric_config_get_uplink_info(self, filename, tftp_addr=None):
        """ Mock fabric_config_get_uplink_info method """
        if not(tftp_addr):
            raise IpmiError('No tftp address!')

        work_dir = tempfile.mkdtemp(prefix="cxmanage_test-")
        # Create uplink info file
        ulinfo = open("%s/%s" % (work_dir, filename), "w")
        for i in range(1, len(self.ip_addresses)):
            ulinfo.write("Node %i: eth0 0, eth1 0, mgmt 0\n" % i)
        ulinfo.close()

        # Upload to tftp
        address, port = tftp_addr.split(":")
        port = int(port)
        tftp = ExternalTftp(address, port)
        tftp.put_file("%s/%s" % (work_dir, filename), filename)

        shutil.rmtree(work_dir)

    def fabric_config_get_uplink(self, iface):
        """ Mock fabric_config_get_uplink """
        return 0

    def fabric_config_get_mac_addresses(self, filename, tftp_addr=None):
        """ Upload a macaddrs file from the node to TFTP"""
        if not(tftp_addr):
            raise IpmiError('No tftp address!')

        work_dir = tempfile.mkdtemp(prefix="cxmanage_test-")

        # Create macaddrs file
        macaddrs = open("%s/%s" % (work_dir, filename), "w")
        for i in range(len(self.ip_addresses)):
            for port in range(3):
                macaddr = "00:00:00:00:%x:%x" % (i, port)
                macaddrs.write("Node %i, Port %i: %s\n" % (i, port, macaddr))
        macaddrs.close()

        # Upload to tftp
        address, port = tftp_addr.split(":")
        port = int(port)
        tftp = ExternalTftp(address, port)
        tftp.put_file("%s/%s" % (work_dir, filename), filename)

        shutil.rmtree(work_dir)

    def fabric_config_get_ip_src(self):
        """ Mock fabric_config_get_ip_src """
        return 2

    def fabric_config_get_ip_addr_base(self):
        """Provide a fake base IP addr"""
        return self.ipaddr_base

    def fabric_get_linkspeed(self, link="", actual=""):
        """ Mock fabric_get_linkspeed """
        return 1

    def fabric_config_get_linkspeed(self):
        """ Mock fabric_config_get_linkspeed """
        return 1

    def fabric_config_get_linkspeed_policy(self):
        """ Mock fabric_config_get_linkspeed_policy """
        return 1

    def fabric_config_get_link_users_factor(self):
        """ Mock fabric_config_get_link_users_factor """
        return 1

    def fabric_config_get_macaddr_base(self):
        """ Mock fabric_config_get_macaddr_base """
        return "00:00:00:00:00:00"

    def fabric_config_get_macaddr_mask(self):
        """ Mock fabric_config_get_macaddr_mask """
        return "00:00:00:00:00:00"

    def fabric_get_uplink_info(self):
        """Corresponds to Node.get_uplink_info()"""
        return 'Node 0: eth0 0, eth1 0, mgmt 0'

    def fabric_get_uplink_speed(self):
        """Corresponds to Node.get_uplink_speed()"""
        return 1

    def fru_read(self, fru_number, filename):
        """ Mock fru_read method """
        with open(filename, "w") as fru_image:
            # Writes a fake FRU image with version "0.0"
            fru_image.write("x00" * 516 + "0.0" + "x00"*7673)

    def pmic_get_version(self):
        """ Mock pmic_get_version method """
        return "0"


class Partition(object):
    """Partition class."""
    def __init__(self, partition, type_, offset=0,
            size=0, priority=0, daddr=0, in_use=None):
        self.updates = 0
        self.retrieves = 0
        self.checks = 0
        self.activates = 0
        self.fwinfo = FWInfoEntry(partition, type_, offset, size, priority,
                                  daddr, in_use)


class FWInfoEntry(object):
    """ Firmware info for a single partition """

    def __init__(self, partition, type_, offset=0, size=0, priority=0, daddr=0,
                  in_use=None):
        self.partition = "%2i" % partition
        self.type = {
                2: "02 (S2_ELF)",
                3: "03 (SOC_ELF)",
                10: "0a (CDB)",
                11: "0b (UBOOTENV)"
            }[type_]
        self.offset = "%8x" % offset
        self.size = "%8x" % size
        self.priority = "%8x" % priority
        self.daddr = "%8x" % daddr
        self.in_use = {None: "Unknown", True: "1", False: "0"}[in_use]
        self.flags = "fffffffd"
        self.version = "v0.0.0"


class Result(object):
    """ Generic result object. Converts kwargs into instance vars """
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

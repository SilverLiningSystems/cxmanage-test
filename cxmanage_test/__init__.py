""" Various objects used by tests """

import random
import shutil
import tempfile

from pyipmi import IpmiError

from cxmanage.tftp import Tftp
from cxmanage.simg import create_simg, get_simg_header

class TestPartition:
    """ A partition on a node """
    def __init__(self, image_type, offset, size, in_use=None, contents=None):
        self.image_type = image_type
        self.offset = offset
        self.size = size
        self.in_use = in_use
        if contents == None:
            raw_contents = "".join([chr(0xFF) for a in range(size - 28)])
            self.contents = create_simg(raw_contents)
        else:
            self.contents = contents

class TestFWInfoResult:
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

class TestCluster:
    """ A cluster of nodes """
    def __init__(self, num_nodes = 1):
        self.nodes = []
        for a in range(num_nodes):
            address = "192.168.100.%i" % (100 + a)
            node = TestNode(address, self)
            self.nodes.append(node)

class TestNode:
    """ A virtual node, with an IP address, partitions, and chassis power """
    def __init__(self, address="192.168.100.250", cluster=None):
        self.address = address
        self.cluster = cluster
        self.partitions = []
        self.power = "off"
        self.policy = "always-off"

        # Add partitions: two S2_ELF, two SOC_ELF/CDB pairs, one running CDB
        self._add_partition(image_type=2, size=20480)
        self._add_partition(image_type=2, size=20480)
        self._add_partition(image_type=3, size=393216, in_use=True)
        self._add_partition(image_type=10, size=196608)
        self._add_partition(image_type=3, size=393216, in_use=False)
        self._add_partition(image_type=10, size=196608)
        self._add_partition(image_type=10, size=196608)

    def _add_partition(self, image_type, size, in_use=None):
        """ Add a partition to this node """
        if len(self.partitions) == 0:
            offset = 0
        else:
            offset = self.partitions[-1].offset + self.partitions[-1].size

        partition = TestPartition(image_type, offset, size, in_use)

        self.partitions.append(partition)

class TestBMC:
    """ BMC handle for a virtual node """
    def __init__(self, node):
        self.node = node

    def get_fabric_ipinfo(self, filename, tftp_address):
        """ Upload an ipinfo file from the node to TFTP"""
        # Set up TFTP client
        tftp = Tftp()
        address, port = tftp_address.split(":")
        port = int(port)
        tftp.set_external_server(address, port)

        # Create file
        work_dir = tempfile.mkdtemp()
        ipinfo_file = open("%s/%s" % (work_dir, filename), "w")
        nodes = self.node.cluster.nodes
        for i in range(len(nodes)):
            address = nodes[i].address
            ipinfo_file.write("Node %i: %s\n" % (i, address))
        ipinfo_file.close()

        # Upload file
        tftp.put_file("%s/%s" % (work_dir, filename), filename)

        # Clean up
        shutil.rmtree(work_dir)

    def set_chassis_power(self, mode):
        """ Set chassis power """
        if mode == "reset":
            if self.node.power == "off":
                raise IpmiError
        else:
            self.node.power = mode

    def get_chassis_status(self):
        """ Get chassis power """
        class Result:
            def __init__(self, power, policy):
                self.power_on = (power == "on")
                self.power_restore_policy = policy

        return Result(self.node.power, self.node.policy)

    def set_chassis_policy(self, mode):
        """ Set chassis restore policy """
        self.node.policy = mode

    def mc_reset(self, mode):
        """ Reset the MC """
        if self.node.policy == "always-off":
            self.node.power = "off"
        elif self.node.policy == "always-on":
            self.node.power = "on"

        class Result:
            pass

        return Result()

    def reset_firmware(self):
        """ Reset the running CDB """
        # TODO
        pass

    def sel_clear(self):
        """ Clear SEL """
        # TODO
        pass

    def get_firmware_info(self):
        """ Get partition and simg info """
        results = []
        for a in range(len(self.node.partitions)):
            partition = self.node.partitions[a]
            header = get_simg_header(partition.contents)
            result = TestFWInfoResult(a, partition.type, partition.offset,
                    partition.size, header.version, header.daddr,
                    partition.in_use)
            results.append(result)

        return results

    def update_firmware(self, filename, slot_id, image_type, tftp_address):
        """ Download a file from a TFTP server to a given slot.

        Make sure the image type matches. """
        # TODO
        pass

    def sdr_list(self):
        """ Get sensor info from the node.

        Virtual node doesn't currently have any sensors, so just make some up.
        """
        class Result:
            def __init__(self, sensor_name, sensor_reading):
                self.sensor_name = sensor_name
                self.sensor_reading = sensor_reading

        power_value = "%f (+/- 0) Watts" % random.uniform(0.0, 10.0)
        temp_value = "%f (+/- 0) degrees C" % random.uniform(30.0, 50.0)
        results = [
                Result("Node Power", power_value),
                Result("Board Temp", temp_value)
        ]
        return results

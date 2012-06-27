import random
import shutil
import tempfile
import unittest

from pyipmi import IpmiError

from cxmanage import CxmanageError
from cxmanage.image import Image
from cxmanage.simg import create_simg, valid_simg, get_simg_header
from cxmanage.target import Target
from cxmanage.tftp import InternalTftp, ExternalTftp

from cxmanage_test import TestSlot, random_file

class TargetTest(unittest.TestCase):
    """ Tests involving cxmanage targets """

    def setUp(self):
        class TestTarget(Target):
            """ A target that uses a test BMC """
            def __init__(self, node):
                Target.__init__(self, node.address, "admin", "admin", 0)
                self.bmc = TestBMC(node)

        self.work_dir = tempfile.mkdtemp()

        # Set up a cluster
        self.cluster = TestCluster(4)
        self.targets = [TestTarget(node) for node in self.cluster.nodes]

        # Set up an internal server
        self.tftp = InternalTftp()

    def tearDown(self):
        shutil.rmtree(self.work_dir)
        self.tftp.kill()

    def test_ipinfo(self):
        """ Test ipinfo command """
        # Get IP info
        ipinfo = self.targets[0].get_ipinfo(self.work_dir, self.tftp)

        # Verify
        for i in range(len(self.targets)):
            self.assertEqual(self.targets[i].address, ipinfo[i])

    def test_power(self):
        """ Test power commands """
        for target in self.targets:
            # Power should be off initially
            self.assertEqual(target.power_status(), "off")

            # Turn power on
            target.power("on")
            self.assertEqual(target.power_status(), "on")

            # Reset
            target.power("reset")
            self.assertEqual(target.power_status(), "on")

            # Turn power off
            target.power("off")
            self.assertEqual(target.power_status(), "off")

            # Try to reset -- should raise an error
            try:
                target.power("reset")
                self.fail()
            except CxmanageError:
                self.assertEqual(target.power_status(), "off")

    def test_policy(self):
        """ Test power policy commands """
        for target in self.targets:
            self.assertEqual(target.power_policy_status(), "always-off")

            target.power_policy("always-on")
            self.assertEqual(target.power_policy_status(), "always-on")

            target.power_policy("previous")
            self.assertEqual(target.power_policy_status(), "previous")

            target.power_policy("always-off")
            self.assertEqual(target.power_policy_status(), "always-off")

    def test_sensor(self):
        """ Test sensor read command """
        for target in self.targets:
            sensors = target.get_sensors()

            # Read node power
            reading = [x.sensor_reading for x in sensors
                    if x.sensor_name == "Node Power"][0]
            value = float(reading.split()[0])
            suffix = reading.lstrip("%f " % value)
            self.assertEqual(suffix, "(+/- 0) Watts")

            # Read board temp
            reading = [x.sensor_reading for x in sensors
                    if x.sensor_name == "Board Temp"][0]
            value = float(reading.split()[0])
            suffix = reading.lstrip("%f " % value)
            self.assertEqual(suffix, "(+/- 0) degrees C")

    def test_config_reset(self):
        """ Test config reset command """
        for target in self.targets:
            # Write random stuff to the partition
            partition = [x for x in target.bmc.node.partitions
                    if x.image_type == 10][-1]
            size = partition.size
            raw_contents = "".join([chr(random.randint(0, 255))
                    for a in range(size - 28)])
            partition.contents = partition.contents[:28] + raw_contents
            self.assertEqual(partition.contents[28:], raw_contents)

            # Reset firmware and check
            target.config_reset()
            raw_contents = "".join([chr(0xFF) for a in range(size - 28)])
            self.assertEqual(partition.contents[28:], raw_contents)

    def test_update_firmware(self):
        """ Test firmware update command """
        class TestImage(Image):
            def valid_type(self):
                return True

        def create_image(partition, image_type):
            filename = random_file(self.work_dir, partition.size - 28)
            contents = open(filename).read()
            return contents, TestImage(filename, image_type, False)

        for target in self.targets:
            # Create random images
            s2_partition = [x for x in target.bmc.node.partitions
                    if x.image_type == 2][1]
            soc_partition = [x for x in target.bmc.node.partitions
                    if x.image_type == 3][1]
            cdb_partition = [x for x in target.bmc.node.partitions
                    if x.image_type == 10][1]
            s2_contents, s2_image = create_image(s2_partition, "S2_ELF")
            soc_contents, soc_image = create_image(soc_partition, "SOC_ELF")
            cdb_contents, cdb_image = create_image(cdb_partition, "CDB")

            # Execute firmware update
            images = [s2_image, soc_image, cdb_image]
            target.update_firmware(self.work_dir,
                    self.tftp, images, "INACTIVE")

            # Examine headers
            changed_partitions = [s2_partition, soc_partition, cdb_partition]
            unchanged_partitions = [x for x in target.bmc.node.partitions
                    if not x in changed_partitions]
            for partition in changed_partitions:
                header = get_simg_header(partition.contents)
                self.assertTrue(valid_simg(partition.contents))
                self.assertEqual(header.version, 1)
            for partition in unchanged_partitions:
                header = get_simg_header(partition.contents)
                self.assertTrue(valid_simg(partition.contents))
                self.assertEqual(header.version, 0)

            # Examine contents
            self.assertEqual(s2_contents, s2_partition.contents[28:])
            self.assertEqual(soc_contents, soc_partition.contents[28:])
            self.assertEqual(cdb_contents, cdb_partition.contents[28:])
            for partition in unchanged_partitions:
                size = partition.size - 28
                contents = "".join([chr(0xFF) for a in range(size)])
                self.assertEqual(partition.contents[28:], contents)


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


class TestNode:
    """ A virtual node, with an IP address, partitions, and chassis power """

    def __init__(self, address="192.168.100.250", cluster=None):
        self.address = address
        self.cluster = cluster
        self.partitions = []
        self.power = "off"
        self.policy = "always-off"

        def add_partition(image_type, size, in_use=None):
            """ Add a partition to this node """
            if len(self.partitions) == 0:
                offset = 0
            else:
                offset = self.partitions[-1].offset + self.partitions[-1].size

            partition = TestPartition(image_type, offset, size, in_use)

            self.partitions.append(partition)

        # Add partitions: two S2_ELF, two SOC_ELF/CDB pairs, one running CDB
        add_partition(image_type=2, size=20480)
        add_partition(image_type=2, size=20480)
        add_partition(image_type=3, size=393216, in_use=True)
        add_partition(image_type=10, size=196608)
        add_partition(image_type=3, size=393216, in_use=False)
        add_partition(image_type=10, size=196608)
        add_partition(image_type=10, size=196608)


class TestCluster:
    """ A cluster of nodes """
    def __init__(self, num_nodes = 1):
        self.nodes = []
        for a in range(num_nodes):
            address = "192.168.100.%i" % (100 + a)
            node = TestNode(address, self)
            self.nodes.append(node)


class TestBMC:
    """ BMC handle for a virtual node """
    def __init__(self, node):
        self.node = node

    def get_fabric_ipinfo(self, filename, tftp_address):
        """ Upload an ipinfo file from the node to TFTP"""
        # Set up TFTP client
        address, port = tftp_address.split(":")
        port = int(port)
        tftp = ExternalTftp(address, port)

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
        partition = [x for x in self.node.partitions if x.image_type == 10][-1]
        size = partition.size
        raw_contents = "".join([chr(0xFF) for a in range(size - 28)])
        partition.contents = (partition.contents[:28] + raw_contents)

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
            result = TestSlot(a, partition.image_type, partition.offset,
                    partition.size, header.version, header.daddr,
                    partition.in_use)
            results.append(result)

        return results

    def update_firmware(self, filename, slot_id, image_type, tftp_address):
        """ Download a file from a TFTP server to a given slot.

        Make sure the image type matches. """

        work_dir = tempfile.mkdtemp()

        partition = self.node.partitions[slot_id]
        image_type = {"S2_ELF": 2, "SOC_ELF": 3, "CDB": 10}[image_type]
        if partition.image_type != image_type:
            raise IpmiError

        # Download from TFTP server
        address, port = tftp_address.split(":")
        port = int(port)
        tftp = ExternalTftp(address, port)
        tftp.get_file(filename, "%s/%s" % (work_dir, filename))

        # Update partition and clean up
        partition.contents = open("%s/%s" % (work_dir, filename)).read()
        shutil.rmtree(work_dir)

        # Return result
        class Result:
            def __init__(self, handle=0):
                self.tftp_handle_id = handle
        return Result()

    def get_firmware_status(self, handle):
        class Result:
            def __init__(self, status=None):
                if status == None:
                    self.status = random.choice(["In progress", "Complete"])
                else:
                    self.status = status
        return Result()

    def check_firmware(self, slot_id):
        class Result:
            def __init__(self, partition):
                header = get_simg_header(partition.contents)
                if valid_simg(partition.contents):
                    self.crc32 = header.crc32
                    self.error = None
                else:
                    # TODO: what's the real error?
                    self.error = True

        return Result(self.node.partitions[slot_id])

    def activate_firmware(self, slot_id):
        partition = self.node.partitions[slot_id]
        header = get_simg_header(partition.contents)
        header.flags = header.flags & 0xFFFFFFFE
        partition.contents = str(header) + partition.contents[28:]

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

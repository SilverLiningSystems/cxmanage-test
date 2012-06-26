import logging
import random
import shutil
import tempfile
import unittest

from tftpy import setLogLevel

from cxmanage import CxmanageError
from cxmanage.image import Image
from cxmanage.simg import get_simg_header, valid_simg
from cxmanage.target import Target
from cxmanage.tftp import Tftp

from cxmanage_test import TestCluster, TestBMC

class TargetTest(unittest.TestCase):
    """ Tests involving cxmanage targets """

    def setUp(self):
        self.work_dir = tempfile.mkdtemp()

        # Set up a cluster
        self.cluster = TestCluster(4)
        self.targets = []
        for node in self.cluster.nodes:
            target = Target(node.address, verbosity=0)
            target.bmc = TestBMC(node)
            self.targets.append(target)

        # Set up an internal server
        self.tftp = Tftp()
        self.tftp.set_internal_server(self.work_dir)
        setLogLevel(logging.ERROR)

    def tearDown(self):
        self.tftp.kill_server()
        shutil.rmtree(self.work_dir)

    def test_ipinfo(self):
        """ Download and verify IP info file """
        filename = "%s/ip_info.txt" % self.work_dir

        # Download IP info file
        self.targets[0].get_fabric_ipinfo(self.tftp, filename)

        # Read file
        lines = open(filename).read().split("\n")
        for i in range(len(self.targets)):
            self.assertEqual(self.targets[i].address, lines[i].split()[-1])

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
            # Read node power
            reading = target.get_sensor("Node Power")
            value = float(reading.split()[0])
            suffix = reading.lstrip("%f " % value)
            self.assertEqual(suffix, "(+/- 0) Watts")

            # Read board temp
            reading = target.get_sensor("Board Temp")
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
            size = partition.size - 28
            contents = "".join([chr(random.randint(0, 255))
                for a in range(size)])
            filename = "%s/%s_image" % (self.work_dir, image_type)
            open(filename, "w").write(contents)
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

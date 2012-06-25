import shutil
import tempfile
import unittest

from cxmanage import CxmanageError
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
            target = Target(node.address)
            target.bmc = TestBMC(node)
            self.targets.append(target)

        # Set up an internal server
        self.tftp = Tftp()
        self.tftp.set_internal_server(self.work_dir)

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

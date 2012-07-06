#Copyright 2012 Calxeda, Inc.  All Rights Reserved.

import random
import time
import unittest

from cxmanage.controller import Controller
from cxmanage_test import TestSensor

num_nodes = 128
addresses = ["192.168.100.%i" % a for a in range(1, num_nodes+1)]

class ControllerTargetTest(unittest.TestCase):
    """ Tests involving the cxmanage controller """

    def setUp(self):
        # Set up the controller
        self.controller = Controller(max_threads=32,
                image_class=DummyImage, target_class=DummyTarget)

    def tearDown(self):
        self.controller.kill()

    def test_add_targets(self):
        """ Test adding targets"""
        # Add targets
        self.assertEqual(len(self.controller.targets), 0)
        for address in addresses:
            self.controller.add_target(address, "admin", "admin")

        # Examine targets
        self.assertEqual(len(addresses), len(self.controller.targets))
        for address in addresses:
            self.assertTrue(any([address == x.address
                    for x in self.controller.targets]))

    def test_add_all_targets(self):
        """ Test adding targets with ipinfo """
        # Add targets
        self.assertEqual(len(self.controller.targets), 0)
        self.controller.add_target(addresses[0], "admin", "admin", True)

        # Examine targets
        self.assertEqual(len(addresses), len(self.controller.targets))
        for address in addresses:
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

    def test_power(self):
        """ Test controller power command """
        # Add targets
        self.controller.add_target(addresses[0], "admin", "admin", True)

        # Send power commands
        modes = ["on", "reset", "off"]
        for mode in modes:
            self.assertFalse(self.controller.power(mode))

        for target in self.controller.targets:
            # Verify commands
            self.assertTrue(len(target.executed), 3)
            self.assertTrue(all([x[0] == "power" for x in target.executed]))
            for a in range(len(modes)):
                self.assertEqual(target.executed[a][1], modes[a])

    def test_power_status(self):
        """ Test controller power status command """
        # Add targets
        self.controller.add_target(addresses[0], "admin", "admin", True)

        # Send power status command
        self.assertFalse(self.controller.power_status())

        for target in self.controller.targets:
            # Verify command
            self.assertTrue(len(target.executed), 1)
            self.assertEqual(target.executed[0], "power_status")

    def test_power_policy(self):
        """ Test controller power policy command """
        # Add targets
        self.controller.add_target(addresses[0], "admin", "admin", True)

        # Send power policy commands
        modes = ["always-on", "previous", "always-off"]
        for mode in modes:
            self.assertFalse(self.controller.power_policy(mode))

        for target in self.controller.targets:
            # Verify commands
            self.assertTrue(len(target.executed), 3)
            self.assertTrue(all([x[0] == "power_policy"
                    for x in target.executed]))
            for a in range(len(modes)):
                self.assertEqual(target.executed[a][1], modes[a])

    def test_power_policy_status(self):
        """ Test controller power policy status command """
        # Add targets
        self.controller.add_target(addresses[0], "admin", "admin", True)

        # Send power policy status command
        self.assertFalse(self.controller.power_policy_status())

        for target in self.controller.targets:
            # Verify command
            self.assertTrue(len(target.executed), 1)
            self.assertEqual(target.executed[0], "power_policy_status")

    def test_mc_reset(self):
        """ Test controller mc reset command """
        # Add targets
        self.controller.add_target(addresses[0], "admin", "admin", True)

        # Send mc reset command
        self.assertFalse(self.controller.mc_reset())

        for target in self.controller.targets:
            # Verify command
            self.assertTrue(len(target.executed), 1)
            self.assertEqual(target.executed[0], "mc_reset")

    def test_get_sensors(self):
        """ Test controller get sensors command """
        # Add targets
        self.controller.add_target(addresses[0], "admin", "admin", True)

        # Send get sensors commands
        self.assertFalse(self.controller.get_sensors())
        self.assertFalse(self.controller.get_sensors("Node Power"))

        for target in self.controller.targets:
            # Verify command
            self.assertTrue(len(target.executed), 2)
            self.assertTrue(all([x == "get_sensors" for x in target.executed]))

    def test_get_ipinfo(self):
        """ Test controller get ipinfo command """
        # Add targets
        self.controller.add_target(addresses[0], "admin", "admin")

        # Send get ipinfo command
        self.assertFalse(self.controller.get_ipinfo())

        for target in self.controller.targets:
            # Verify command
            self.assertTrue(len(target.executed), 1)
            self.assertEqual(target.executed[0], "get_ipinfo")

    def test_get_macaddrs(self):
        """ Test controller get macaddrs command """
        # Add targets
        self.controller.add_target(addresses[0], "admin", "admin")

        # Send get macaddrs command
        self.assertFalse(self.controller.get_macaddrs())

        for target in self.controller.targets:
            # Verify command
            self.assertTrue(len(target.executed), 1)
            self.assertEqual(target.executed[0], "get_macaddrs")

    def test_config_reset(self):
        """ Test controller config reset command """
        # Add targets
        self.controller.add_target(addresses[0], "admin", "admin", True)

        # Send config reset command
        self.assertFalse(self.controller.config_reset())

        for target in self.controller.targets:
            # Verify command
            self.assertTrue(len(target.executed), 1)
            self.assertEqual(target.executed[0], "config_reset")

    def test_ipmitool_command(self):
        """ Test controller ipmitool command """
        # Add targets
        self.controller.add_target(addresses[0], "admin", "admin", True)

        # Send ipmitool command
        ipmitool_args = ["chassis", "status"]
        self.assertFalse(self.controller.ipmitool_command(ipmitool_args))

        for target in self.controller.targets:
            # Verify command
            self.assertTrue(len(target.executed), 1)
            self.assertEqual(target.executed[0][0], "ipmitool_command")
            self.assertEqual(target.executed[0][1], ipmitool_args)

    def test_firmware_update(self):
        """ Test controller firmware update command """
        # Add targets and images
        self.controller.add_target(addresses[0], "admin", "admin", True)
        self.controller.add_image("stage2boot.bin", "S2_ELF")
        self.controller.add_image("socmanager.elf", "SOC_ELF")
        self.controller.add_image("factory.cdb", "CDB")

        # Perform firmware update
        self.assertFalse(self.controller.update_firmware(skip_reset=True))

        for target in self.controller.targets:
            # Check updated types
            self.assertEqual(len(target.executed), 1)
            self.assertEqual(target.executed[0][0], "update_firmware")
            updated_types = [x.type for x in target.executed[0][1]]
            for image_type in ["S2_ELF", "SOC_ELF", "CDB"]:
                self.assertTrue(image_type in updated_types)


class DummyTarget:
    """ Dummy target for the controller tests """
    def __init__(self, address, *args):
        self.address = address
        self.executed = []

    def get_ipinfo(self, work_dir, tftp):
        self.executed.append("get_ipinfo")
        return list(enumerate(addresses))

    def get_macaddrs(self, work_dir, tftp):
        self.executed.append("get_macaddrs")
        # TODO: return real mac addresses
        return [(a, 0, addresses[a]) for a in range(num_nodes)]

    def power(self, mode):
        self.executed.append(("power", mode))

    def power_status(self):
        self.executed.append("power_status")
        return "off"

    def power_policy(self, mode):
        self.executed.append(("power_policy", mode))

    def power_policy_status(self):
        self.executed.append("power_policy_status")
        return "always-off"

    def mc_reset(self):
        self.executed.append("mc_reset")

    def update_firmware(self, work_dir, tftp, images, slot_arg):
        self.executed.append(("update_firmware", images))
        time.sleep(random.randint(0, 2))

    def get_sensors(self):
        self.executed.append("get_sensors")
        power_value = "%f (+/- 0) Watts" % random.uniform(0, 10)
        temp_value = "%f (+/- 0) degrees C" % random.uniform(30, 50)
        sensors = [
                TestSensor("Node Power", power_value),
                TestSensor("Board Temp", temp_value)
        ]
        return sensors

    def config_reset(self):
        self.executed.append("config_reset")

    def ipmitool_command(self, ipmitool_args):
        self.executed.append(("ipmitool_command", ipmitool_args))


class DummyImage:
    def __init__(self, filename, image_type, *args):
        self.filename = filename
        self.type = image_type

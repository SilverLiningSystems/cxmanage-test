import random
import time
import unittest

from cxmanage.controller import Controller

class ControllerTest(unittest.TestCase):
    """ Tests involving the cxmanage controller """

    def setUp(self):
        class DummyTarget:
            """ Dummy target for the controller tests """
            def __init__(self, address, username="admin", password="admin", verbosity=0):
                self.address = address
                self.updated_image_types = []

            def get_ipinfo(self, work_dir, tftp):
                return addresses

            def update_firmware(self, work_dir, tftp, images, slot_arg):
                time.sleep(random.randint(0, 5))
                for image in images:
                    self.updated_image_types.append(image.type)

        class DummyImage:
            def __init__(self, filename, image_type, simg=None,
                    version=None, daddr=None, skip_crc32=False):
                self.filename = filename
                self.type = image_type

        addresses = ["192.168.100.100", "192.168.100.101",
                "192.168.100.102", "192.168.100.103"]
        self.addresses = addresses

        # Set up the controller
        self.controller = Controller(image_class=DummyImage,
                target_class=DummyTarget)

    def tearDown(self):
        self.controller.kill()

    def test_add_targets(self):
        """ Test adding targets"""
        # Add targets
        self.assertEqual(len(self.controller.targets), 0)
        for address in self.addresses:
            self.controller.add_target(address, "admin", "admin")

        # Examine targets
        self.assertEqual(len(self.addresses), len(self.controller.targets))
        for address in self.addresses:
            self.assertTrue(any([address == x.address
                    for x in self.controller.targets]))

    def test_add_all_targets(self):
        """ Test adding targets with ipinfo """
        # Add targets
        self.assertEqual(len(self.controller.targets), 0)
        self.controller.add_target(self.addresses[0], "admin", "admin", True)

        # Examine targets
        self.assertEqual(len(self.addresses), len(self.controller.targets))
        for address in self.addresses:
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

    def test_firmware_update(self):
        """ Test controller firmware update """
        # Add targets and images
        self.controller.add_target(self.addresses[0], "admin", "admin", True)
        self.controller.add_image("stage2boot.bin", "S2_ELF")
        self.controller.add_image("socmanager.elf", "SOC_ELF")
        self.controller.add_image("factory.cdb", "CDB")

        # Perform firmware update
        self.assertFalse(self.controller.update_firmware(skip_reset=True))

        for address in self.addresses:
            # Get corresponding target
            target = [x for x in self.controller.targets
                    if x.address == address][0]

            # Check updated types
            self.assertEqual(len(target.updated_image_types), 3)
            for image_type in ["S2_ELF", "SOC_ELF", "CDB"]:
                self.assertTrue(image_type in target.updated_image_types)

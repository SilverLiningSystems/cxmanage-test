#Copyright 2012 Calxeda, Inc.  All rights reserved.

""" Target objects used by the cxmanage controller """

import os
import subprocess
import tempfile
import time

from cxmanage import CxmanageError
from cxmanage.image import Image
from cxmanage.ubootenv import UbootEnv

from pyipmi import make_bmc, IpmiError
from pyipmi.bmc import LanBMC

class Target:
    """ Contains info for a single target. A target consists of a hostname,
    an username, and a password. """

    def __init__(self, address, username="admin",
            password="admin", verbosity=0):
        self.address = address
        self.username = username
        self.password = password
        self.verbosity = verbosity

        verbose = verbosity >= 2
        self.bmc = make_bmc(LanBMC, hostname=address,
                username=username, password=password, verbose=verbose)

    def get_ipinfo(self, work_dir, tftp):
        """ Download IP info from this target """
        tftp_address = "%s:%s" % (tftp.get_address(self.address),
                tftp.get_port())

        filename = tempfile.mkstemp(prefix="%s/ip_" % work_dir)[1]
        basename = os.path.basename(filename)

        # Send ipinfo command
        try:
            self.bmc.get_fabric_ipinfo(basename, tftp_address)
        except IpmiError:
            raise CxmanageError("Failed to retrieve IP info")

        # Wait for file
        for a in range(10):
            try:
                time.sleep(1)
                tftp.get_file(basename, filename)
                if os.path.getsize(filename) > 0:
                    break
            except CxmanageError:
                pass

        # Ensure file is present
        if not os.path.exists(filename):
            raise CxmanageError("Failed to retrieve IP info")

        # Parse addresses from ipinfo file
        results = []
        for line in open(filename):
            if line.startswith("Node"):
                elements = line.split()
                node = int(elements[1].rstrip(":"))
                address = elements[2]
                if address != "0.0.0.0":
                    results.append((node, address))

        # Make sure we found something
        if len(results) == 0:
            raise CxmanageError("Failed to retrieve IP info")

        return results

    def get_macaddrs(self, work_dir, tftp):
        """ Download mac addresses from this target """
        tftp_address = "%s:%s" % (tftp.get_address(self.address),
                tftp.get_port())

        filename = tempfile.mkstemp(prefix="%s/mac_" % work_dir)[1]
        basename = os.path.basename(filename)

        # Send ipinfo command
        try:
            self.bmc.get_fabric_macaddresses(basename, tftp_address)
        except IpmiError:
            raise CxmanageError("Failed to retrieve mac addresses")

        # Wait for file
        for a in range(10):
            try:
                time.sleep(1)
                tftp.get_file(basename, filename)
                if os.path.getsize(filename) > 0:
                    break
            except CxmanageError:
                pass

        # Ensure file is present
        if not os.path.exists(filename):
            raise CxmanageError("Failed to retrieve mac addresses")

        # Parse addresses from ipinfo file
        results = []
        for line in open(filename):
            if line.startswith("Node"):
                elements = line.split()
                node = int(elements[1].rstrip(","))
                port = int(elements[3].rstrip(":"))
                address = elements[4]
                results.append((node, port, address))

        # Make sure we found something
        if len(results) == 0:
            raise CxmanageError("Failed to retrieve mac addresses")

        return results

    def power(self, mode):
        """ Send an IPMI power command to this target """
        try:
            self.bmc.set_chassis_power(mode=mode)
        except IpmiError:
            raise CxmanageError("Failed to send power %s command" % mode)

    def power_policy(self, state):
        """ Set default power state for A9 """
        try:
            self.bmc.set_chassis_policy(state)
        except IpmiError:
            raise CxmanageError("Failed to set power policy to \"%s\"" % state)

    def power_policy_status(self):
        """ Return power status reported by IPMI """
        try:
            return self.bmc.get_chassis_status().power_restore_policy
        except IpmiError:
            raise CxmanageError("Failed to retrieve power status")

    def power_status(self):
        """ Return power status reported by IPMI """
        try:
            if self.bmc.get_chassis_status().power_on:
                return "on"
            else:
                return "off"
        except IpmiError:
            raise CxmanageError("Failed to retrieve power status")

    def mc_reset(self):
        """ Send an IPMI MC reset command to the target """
        try:
            result = self.bmc.mc_reset("cold")
            if hasattr(result, "error"):
                raise CxmanageError("Failed to send MC reset command")
        except IpmiError:
            raise CxmanageError("Failed to send MC reset command")

    def get_sensors(self):
        """ Get a list of sensor (name, reading) tuples from this target """
        try:
            return self.bmc.sdr_list()
        except IpmiError:
            raise CxmanageError("Failed to retrieve sensor value")

    def get_firmware_info(self):
        """ Get firmware info from the target """
        try:
            fwinfo = [x for x in self.bmc.get_firmware_info()
                    if hasattr(x, "slot")]

            # Flag CDB as "in use" based on socman info
            for a in range(1, len(fwinfo)):
                previous = fwinfo[a-1]
                slot = fwinfo[a]
                if (slot.type.split()[1][1:-1] == "CDB" and
                        slot.in_use == "Unknown"):
                    if previous.type.split()[1][1:-1] != "SOC_ELF":
                        slot.in_use = "1"
                    else:
                        slot.in_use = previous.in_use

            return fwinfo

        except IpmiError:
            raise CxmanageError("Failed to retrieve firmware info")

    def update_firmware(self, work_dir, tftp, images, slot_arg):
        """ Update firmware on this target. """
        fwinfo = self.get_firmware_info()

        for image in images:
            if image.type == "UBOOTENV":
                # Get slots
                inactive_slot = self._get_slot(fwinfo, image.type, "INACTIVE")
                active_slot = self._get_slot(fwinfo, image.type, "ACTIVE")

                # Update inactive ubootenv
                self._upload_image(work_dir, tftp, image, inactive_slot,
                        int(inactive_slot.version, 16))

                # Update active ubootenv
                old_ubootenv = self._download_ubootenv(work_dir,
                        tftp, active_slot)
                bootcmd = old_ubootenv.get_variable("bootcmd0")
                if image.simg:
                    ubootenv = UbootEnv(open(image.filename).read()[28:])
                else:
                    ubootenv = UbootEnv(open(image.filename).read())
                ubootenv.set_variable("bootcmd0", bootcmd)
                self._upload_ubootenv(work_dir, tftp, active_slot, ubootenv)

            else:
                # Get the slots
                if slot_arg == "BOTH":
                    slots = [self._get_slot(fwinfo, image.type, "FIRST"),
                            self._get_slot(fwinfo, image.type, "SECOND")]
                else:
                    slots = [self._get_slot(fwinfo, image.type, slot_arg)]

                # Get the new version
                versions = [int(x.version, 16) for x in fwinfo if
                        x.type.split()[1][1:-1] == image.type]
                # Assume 0xFFFF comes from an invalid partition
                versions = [x for x in versions if x != 0xFFFF]
                if len(versions) > 0:
                    new_version = min(0xFFFF, max(versions) + 1)
                else:
                    new_version = 0

                # Update the image
                for slot in slots:
                    self._upload_image(work_dir, tftp, image, slot, new_version)

    def config_reset(self, work_dir, tftp):
        """ Reset configuration to factory default """
        try:
            # Reset CDB
            result = self.bmc.reset_firmware()
            if hasattr(result, "error"):
                raise CxmanageError("Failed to reset configuration")

            # Reset ubootenv
            fwinfo = self.get_firmware_info()
            inactive_slot = self._get_slot(fwinfo, "UBOOTENV", "INACTIVE")
            active_slot = self._get_slot(fwinfo, "UBOOTENV", "ACTIVE")
            image = self._download_image(work_dir, tftp, inactive_slot)
            self._upload_image(work_dir, tftp, image, active_slot)

            # Clear SEL
            self.bmc.sel_clear()

        except IpmiError:
            raise CxmanageError("Failed to reset configuration")

    def config_boot(self, work_dir, tftp, boot_args):
        """ Configure boot order """
        fwinfo = self.get_firmware_info()
        slot = self._get_slot(fwinfo, "UBOOTENV", "ACTIVE")

        # Download, modify, and reupload ubootenv
        ubootenv = self._download_ubootenv(work_dir, tftp, slot)
        ubootenv.set_boot_order(boot_args)
        self._upload_ubootenv(work_dir, tftp, slot, ubootenv)

    def config_boot_status(self, work_dir, tftp):
        """ Get boot order """
        fwinfo = self.get_firmware_info()
        slot = self._get_slot(fwinfo, "UBOOTENV", "ACTIVE")

        # Download and read boot order
        ubootenv = self._download_ubootenv(work_dir, tftp, slot)
        return ubootenv.get_boot_order()

    def ipmitool_command(self, ipmitool_args):
        """ Execute an arbitrary ipmitool command """
        command = ["ipmitool", "-U", self.username, "-P", self.password, "-H",
                self.address]
        command += ipmitool_args

        if self.verbosity >= 2:
            print "Running %s" % " ".join(command)
        subprocess.call(command)

    def _get_slot(self, fwinfo, image_type, slot_arg):
        """ Get a slot for this image type based on the slot argument """
        # Filter slots for this type
        slots = [x for x in fwinfo if x.type.split()[1][1:-1] == image_type]
        if len(slots) < 1:
            raise CxmanageError("No slots found on host")

        if slot_arg == "FIRST":
            return slots[0]
        elif slot_arg == "SECOND":
            if len(slots) < 2:
                raise CxmanageError("No second slot found on host")
            return slots[1]
        elif slot_arg == "THIRD":
            if len(slots) < 3:
                raise CxmanageError("No third slot found on host")
            return slots[2]
        elif slot_arg == "OLDEST":
            # Choose second slot if both are the same version
            if len(slots) == 1 or slots[0].version < slots[1].version:
                return slots[0]
            else:
                return slots[1]
        elif slot_arg == "NEWEST":
            # Choose first slot if both are the same version
            if len(slots) == 1 or slots[0].version >= slots[1].version:
                return slots[0]
            else:
                return slots[1]
        elif slot_arg == "INACTIVE":
            # Get inactive slots
            slots = [x for x in slots if x.in_use != "1"]
            if len(slots) < 1:
                raise CxmanageError("No inactive slots found on host")

            # Choose second slot if both are the same version
            if len(slots) == 1 or slots[0].version < slots[1].version:
                return slots[0]
            else:
                return slots[1]
        elif slot_arg == "ACTIVE":
            # Get active slots
            slots = [x for x in slots if x.in_use != "0"]
            if len(slots) < 1:
                raise CxmanageError("No active slots found on host")

            # Choose first slot if both are the same version
            if len(slots) == 1 or slots[0].version >= slots[1].version:
                return slots[0]
            else:
                return slots[1]
        else:
            raise ValueError("Invalid slot argument: %s" % slot_arg)

    def _upload_image(self, work_dir, tftp, image, slot, new_version=0):
        """ Upload a single image. This includes uploading the image,
        performing the firmware update, crc32 check, and activation."""
        tftp_address = "%s:%s" % (tftp.get_address(self.address),
                tftp.get_port())

        # Upload image to tftp server
        filename = image.upload(work_dir, tftp, slot, new_version)

        # Send firmware update command
        slot_id = int(slot.slot)
        image_type = image.type
        result = self.bmc.update_firmware(filename,
                slot_id, image_type, tftp_address)
        handle = result.tftp_handle_id

        # Wait for update to finish
        self._wait_for_transfer(handle)

        # Verify crc
        result = self.bmc.check_firmware(slot_id)
        if hasattr(result, "crc32") and result.error == None:
            # Activate
            self.bmc.activate_firmware(slot_id)
        else:
            raise CxmanageError("Node reported crc32 check failure")

    def _download_image(self, work_dir, tftp, slot):
        """ Download an image from the target.

        Returns the filename. """
        tftp_address = "%s:%s" % (tftp.get_address(self.address),
                tftp.get_port())

        # Download the image
        filename = tempfile.mkstemp(prefix="%s/img_" % work_dir)[1]
        basename = os.path.basename(filename)
        image_type = slot.type.split()[1][1:-1]
        handle = self.bmc.retrieve_firmware(basename,
                int(slot.slot), image_type, tftp_address).tftp_handle_id
        self._wait_for_transfer(handle)
        tftp.get_file(basename, filename)

        return Image(filename, image_type)

    def _upload_ubootenv(self, work_dir, tftp, slot, ubootenv):
        """ Upload a uboot environment to the target """
        filename = tempfile.mkstemp(prefix="%s/env_" % work_dir)[1]
        open(filename, "w").write(ubootenv.get_contents())
        image = Image(filename, "UBOOTENV", version=int(slot.version, 16),
                daddr=int(slot.daddr, 16))
        self._upload_image(work_dir, tftp, image, slot)

    def _download_ubootenv(self, work_dir, tftp, slot):
        """ Download a uboot environment from the target """
        image = self._download_image(work_dir, tftp, slot)

        # Open the file
        simg = open(image.filename).read()
        return UbootEnv(simg[28:])

    def _wait_for_transfer(self, handle):
        """ Wait for a firmware transfer to finish"""

        while True:
            time.sleep(1)
            result = self.bmc.get_firmware_status(handle)
            if not hasattr(result, "status"):
                raise CxmanageError("Unable to retrieve transfer info")
            if result.status != "In progress":
                break
        if result.status != "Complete":
            raise CxmanageError("Node reported transfer failure")

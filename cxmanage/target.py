#Copyright 2012 Calxeda, Inc.  All rights reserved.

""" Target objects used by the cxmanage controller """

import os
import subprocess
import sys
import time

from cxmanage import CxmanageError

from pyipmi import make_bmc, IpmiError
from pyipmi.bmc import LanBMC

class Target:
    """ Contains info for a single target. A target consists of a hostname,
    an username, and a password. """

    def __init__(self, address, username="admin",
            password="admin", verbosity=1):
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

        filename = "%s/ip_%s" % (work_dir, self.address)
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

        filename = "%s/mac_%s" % (work_dir, self.address)
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

    def update_firmware(self, work_dir, tftp, images, slot_arg):
        """ Update firmware on this target. """
        # Get all updates
        plan = self._get_update_plan(images, slot_arg)
        for image, slot, new_version in plan:
            self._update_image(work_dir, tftp, image, slot, new_version)

    def get_sensors(self):
        """ Get a list of sensor (name, reading) tuples from this target """
        try:
            return self.bmc.sdr_list()
        except IpmiError:
            raise CxmanageError("Failed to retrieve sensor value")

    def config_reset(self):
        """ Reset configuration to factory default """
        try:
            # Reset CDB
            result = self.bmc.reset_firmware()
            if hasattr(result, "error"):
                raise CxmanageError("Failed to reset configuration")

            # Clear SEL
            self.bmc.sel_clear()

        except IpmiError:
            raise CxmanageError("Failed to reset configuration")

    def ipmitool_command(self, ipmitool_args):
        """ Execute an arbitrary ipmitool command """
        command = ["ipmitool", "-U", self.username, "-P", self.password, "-H",
                self.address]
        command += ipmitool_args

        if self.verbosity >= 2:
            print "Running %s" % " ".join(command)
        subprocess.call(command)

    def _get_update_plan(self, images, slot_arg):
        """ Get an update plan.

        A plan consists of a list of tuples:
        (image, slot, version) """
        plan = []

        # Get all slots
        try:
            slots = [x for x in self.bmc.get_firmware_info()
                    if hasattr(x, "slot")]
        except IpmiError:
            raise CxmanageError("Failed to retrieve firmware info")
        if not slots:
            raise CxmanageError("Failed to retrieve firmware info")

        soc_plan_made = False
        cdb_plan_made = False
        for image in images:
            if soc_plan_made and image.type == "CDB":
                for update in plan:
                    if update[0].type == "SOC_ELF":
                        slot = slots[int(update[1].slot) + 1]
                        plan.append((image, slot, update[2]))
            elif cdb_plan_made and image.type == "SOC_ELF":
                for update in plan:
                    if update[0].type == "CDB":
                        slot = slots[int(update[1].slot) - 1]
                        plan.append((image, slot, update[2]))
            else:
                # Filter slots for this type
                type_slots = [x for x in slots if
                        x.type.split()[1][1:-1] == image.type]
                if len(type_slots) < 1:
                    raise CxmanageError("No slots found on host")

                versions = [int(x.version, 16) for x in type_slots]
                versions = [x for x in versions if x != 0xFFFF]
                new_version = 0
                if len(versions) > 0:
                    new_version = min(0xffff, max(versions) + 1)

                if slot_arg == "FIRST":
                    plan.append((image, type_slots[0], new_version))
                elif slot_arg == "SECOND":
                    if len(type_slots) < 2:
                        raise CxmanageError("No second slot found on host")
                    plan.append((image, type_slots[1], new_version))
                elif slot_arg == "THIRD":
                    if len(type_slots) < 3:
                        raise CxmanageError("No third slot found on host")
                    plan.append((image, type_slots[2], new_version))
                elif slot_arg == "BOTH":
                    if len(type_slots) < 2:
                        raise CxmanageError("No second slot found on host")
                    plan.append((image, type_slots[0], new_version))
                    plan.append((image, type_slots[1], new_version))
                elif slot_arg == "OLDEST":
                    # Choose second slot if both are the same version
                    if (len(type_slots) == 1 or
                            type_slots[0].version < type_slots[1].version):
                        slot = type_slots[0]
                    else:
                        slot = type_slots[1]
                    plan.append((image, slot, new_version))
                elif slot_arg == "NEWEST":
                    # Choose first slot if both are the same version
                    if (len(type_slots) == 1 or
                            type_slots[0].version >= type_slots[1].version):
                        slot = type_slots[0]
                    else:
                        slot = type_slots[1]
                    plan.append((image, slot, new_version))
                elif slot_arg == "INACTIVE":
                    # Get inactive slots
                    inactive_slots = [x for x in type_slots if x.in_use != "1"]
                    if len(inactive_slots) < 1:
                        raise CxmanageError("No inactive slots found on host")

                    # Choose second slot if both are the same version
                    if (len(inactive_slots) == 1 or inactive_slots[0].version
                            < inactive_slots[1].version):
                        slot = inactive_slots[0]
                    else:
                        slot = inactive_slots[1]
                    plan.append((image, slot, new_version))
                else:
                    raise ValueError("Invalid slot argument: %s" % slot_arg)

                if image.type == "SOC_ELF":
                    soc_plan_made = True
                elif image.type == "CDB_ELF":
                    cdb_plan_made = True

        return plan

    def _update_image(self, work_dir, tftp, image, slot, new_version):
        """ Update a single image. This includes uploading the image,
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
        while True:
            time.sleep(1)
            result = self.bmc.get_firmware_status(handle)
            if not hasattr(result, "status"):
                raise CxmanageError("Unable to retrieve transfer info")
            if result.status != "In progress":
                break

        # Activate firmware on completion
        if result.status == "Complete":
            # Verify crc
            result = self.bmc.check_firmware(slot_id)
            if hasattr(result, "crc32") and result.error == None:
                # Activate
                self.bmc.activate_firmware(slot_id)
            else:
                raise CxmanageError("Node reported crc32 check failure")
        else:
            raise CxmanageError("Node reported transfer failure")

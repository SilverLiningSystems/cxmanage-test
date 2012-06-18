#Copyright 2012 Calxeda, Inc.  All rights reserved.

""" Target objects used by the cxmanage controller """

import os
import socket
import subprocess
import time

from pyipmi import make_bmc, IpmiError
from pyipmi.bmc import LanBMC

class Target:
    """ Contains info for a single target. A target consists of a hostname,
    an username, and a password. """

    def __init__(self, address, username, password, verbosity):
        self.address = address
        self.username = username
        self.password = password
        self.verbosity = verbosity

        verbose = verbosity > 1
        self.bmc = make_bmc(LanBMC, hostname=address,
                username=username, password=password, verbose=verbose)

    def get_fabric_ipinfo(self, tftp, filename):
        """ Download IP info from this target """
        try:
            tftp_address = self._get_tftp_address(tftp)
            basename = os.path.basename(filename)
            self.bmc.get_fabric_ipinfo(basename, tftp_address)
            time.sleep(1)
            tftp.get_file(basename, filename)
            if not os.path.exists(filename):
                raise ValueError
        except:
            raise ValueError("Failed to retrieve IP info")

    def power(self, mode):
        """ Send an IPMI power command to this target """
        try:
            self.bmc.set_chassis_power(mode=mode)
        except IpmiError:
            raise ValueError("Failed to send power %s command" % mode)

    def power_policy(self, state):
        """ Set default power state for A9 """
        try:
            self.bmc.set_chassis_policy(state)
        except IpmiError:
            raise ValueError("Failed to set power policy to \"%s\"" % state)

    def power_status(self):
        """ Return power status reported by IPMI """
        try:
            if self.bmc.get_chassis_status().power_on:
                return "on"
            else:
                return "off"
        except IpmiError:
            raise ValueError("Failed to retrieve power status")

    def mc_reset(self):
        """ Send an IPMI MC reset command to the target """
        try:
            self.bmc.mc_reset("cold")
        except IpmiError:
            raise ValueError("Failed to send MC reset command")

    def update_firmware(self, work_dir, tftp, images, slot_arg):
        """ Update firmware on this target. """
        # Get all updates
        plan = self._get_update_plan(images, slot_arg)
        for image, slot, new_version in plan:
            self._update_image(work_dir, tftp, image, slot, new_version)

    def set_ecc(self, mode):
        """ Enable ECC on this target """
        try:
            # Get value
            if mode == "on":
                value = "01000000"
            elif mode == "off":
                value = "00000000"
            else:
                raise ValueError("\"%s\" is not a valid ECC mode" % mode)

            # Write to CDB and verify
            self.bmc.cdb_write(4, "02000002", value)
            result = self.bmc.cdb_read(4, "02000002")
            if not hasattr(result, "value") or result.value != value:
                raise ValueError("Failed to set ECC to \"%s\"" % mode)
        except IpmiError:
            raise ValueError("Failed to set ECC to \"%s\"" % mode)

    def get_sensor(self, name):
        """ Read a sensor value from this target """
        try:
            sensors = [x for x in self.bmc.sdr_list() if x.sensor_name == name]
            if len(sensors) < 1:
                raise ValueError("Sensor \"%s\" not found" % name)
            return sensors[0].sensor_reading
        except IpmiError:
            raise ValueError("Failed to retrieve sensor value")

    def ipmitool_command(self, ipmitool_args):
        """ Execute an arbitrary ipmitool command """
        command = ["ipmitool", "-U", self.username, "-P", self.password, "-H",
                self.address]
        command += ipmitool_args
        if self.verbose:
            print "Running %s" % " ".join(command)
        subprocess.call(command)

    def _get_tftp_address(self, tftp):
        """ Get the TFTP server address
        Returns a string in ip:port format """
        # Get address
        if tftp.is_internal() and tftp.get_address() == None:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect((self.address, 0))
            address = s.getsockname()[0]
            s.close()
        else:
            address = tftp.get_address()

        # Get port
        port = tftp.get_port()

        # Return in address:port form
        return "%s:%i" % (address, port)

    def _get_update_plan(self, images, slot_arg):
        """ Get an update plan.

        A plan consists of a list of tuples:
        (image, slot, version) """
        plan = []

        # Get all slots
        slots = [x for x in self.bmc.get_firmware_info() if hasattr(x, "slot")]
        if not slots:
            raise ValueError("Failed to retrieve firmware info")

        soc_plan_made = False
        cdb_plan_made = False
        for image in images:
            if image.type == "SPIF":
                # Add all slots
                for slot in slots:
                    plan.append((image, slot, 0))
            elif soc_plan_made and image.type == "CDB":
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
                    raise ValueError("No slots found on host")

                new_version = max([int(x.version, 16) for x in type_slots]) + 1

                if slot_arg == "FIRST":
                    plan.append((image, type_slots[0], new_version))
                elif slot_arg == "SECOND":
                    if len(type_slots) < 2:
                        raise ValueError("No second slot found on host")
                    plan.append((image, type_slots[1], new_version))
                elif slot_arg == "THIRD":
                    if len(type_slots) < 3:
                        raise ValueError("No third slot found on host")
                    plan.append((image, type_slots[2], new_version))
                elif slot_arg == "BOTH":
                    if len(type_slots) < 2:
                        raise ValueError("No second slot found on host")
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
                        raise ValueError("No inactive slots found on host")

                    # Choose second slot if both are the same version
                    if (len(inactive_slots) == 1 or inactive_slots[0].version
                            < inactive_slots[1].version):
                        slot = inactive_slots[0]
                    else:
                        slot = inactive_slots[1]
                    plan.append((image, slot, new_version))
                else:
                    raise ValueError("Invalid slot argument")

                if image.type == "SOC_ELF":
                    soc_plan_made = True
                elif image.type == "CDB_ELF":
                    cdb_plan_made = True

        return plan

    def _update_image(self, work_dir, tftp, image, slot, new_version):
        """ Update a single image. This includes uploading the image,
        performing the firmware update, crc32 check, and activation."""
        tftp_address = self._get_tftp_address(tftp)

        # Upload image to tftp server
        filename = image.upload(work_dir, tftp, slot, new_version)

        # Send firmware update command
        slot_id = int(slot.slot)
        image_type = image.type
        if image_type == "SPIF":
            image_type = slot.type.split()[1][1:-1]
        result = self.bmc.update_firmware(filename,
                slot_id, image_type, tftp_address)
        handle = result.tftp_handle_id

        if image_type == "CDB":
            time.sleep(9)

        # Wait for update to finish
        time.sleep(1)
        status = self.bmc.get_firmware_status(handle).status
        while status == "In progress":
            time.sleep(1)
            status = self.bmc.get_firmware_status(handle).status

        # Activate firmware on completion
        if status == "Complete":
            if image.type != "SPIF":
                # Verify crc
                result = self.bmc.check_firmware(slot_id)
                if hasattr(result, "crc32") and not result.error != None:
                    # Activate
                    self.bmc.activate_firmware(slot_id)
                else:
                    raise ValueError("Node reported crc32 check failure")
        else:
            raise ValueError("Node reported transfer failure")

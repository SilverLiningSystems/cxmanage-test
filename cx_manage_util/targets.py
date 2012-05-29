#!/bin/env python

""" This class is a container of target Calxeda SoCs targeted for configuration
and provisioning. """

import time

from pyipmi import make_bmc
from pyipmi.bmc import LanBMC

class Targets:

    def __init__(self):
        # This is a mapping of group names to address sets
        self._groups = {}

    def add_target_to_group(self, group, addr):
        """ Add the target address to a group """

        # Create group if it doesn't exist
        if not group in self._groups:
            self._groups[group] = set()

        # Add target to group
        self._groups[group].add(addr)

    def get_groups(self):
        """ Return a sorted list of the current groups """
        return sorted(self._groups.keys())

    def get_targets_in_group(self, group):
        """ Return a sorted list of targets in a group """
        return sorted(self._groups[group])

    def delete_group(self, group):
        """ Delete the specified target group """
        del self._groups[group]

    def group_exists(self, group):
        """ Returns true if the specified group exists """
        return group in self._groups

class Target:
    def __init__(self, address, username, password):
        self._address = address
        self._username = username
        self._password = password
        self._bmc = make_bmc(LanBMC, hostname=address,
                username=username, password=password)

    def get_fabric_ipinfo(self, filename, tftp_address):
        self._bmc.get_fabric_ipinfo(filename, tftp_address)

    def power_command(self, command):
        self._bmc.handle.chassis_control(mode=command)

    def update_firmware(self, image_type, filename, tftp_address):
        # Get slots
        results = self._bmc.get_firmware_info()[:-1]
        try:
            # Image type is an int
            slots = [x.slot for x in results[:-1] if
                    int(x.type.split()[0]) == int(image_type)]
        except ValueError:
            # Image type is a string
            slots = [x.slot for x in results[:-1] if
                    x.type.split()[1][1:-1] == image_type.upper()]

        # TODO: should we apply to all slots?
        # For now, apply only to first
        slots = slots[:1]

        for slot in slots:
            # Send firmware update command
            result = self._bmc.update_firmware(filename,
                    slot, image_type, tftp_address)
            handle = result.tftp_handle_id
        
            # Wait for update to finish
            time.sleep(1)
            status = self._bmc.get_firmware_status(handle).status
            while status == "In progress":
                time.sleep(1)
                status = self._bmc.get_firmware_status(handle).status

            # TODO: look at final status
            # For now, activate firmware
            self._bmc.activate_firmware(slot)

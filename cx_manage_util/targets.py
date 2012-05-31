#!/bin/env python

""" This class is a container of target Calxeda SoCs targeted for configuration
and provisioning. """

import time

from pyipmi import make_bmc
from pyipmi.bmc import LanBMC

class Targets:
    """ Contains a list of targets """

    def __init__(self):
        # This is a mapping of group names to address sets
        self._groups = {}

    def add_target(self, group, address, username, password):
        """ Add the target address to a group """

        # Create group if it doesn't exist
        if not group in self._groups:
            self._groups[group] = set()

        # Add target to group
        self._groups[group].add(Target(address, username, password))

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
    """ Contains info for a single target. A target consists of a hostname,
    an username, and a password. """

    def __init__(self, address, username, password):
        self._address = address
        self._username = username
        self._password = password
        self._bmc = make_bmc(LanBMC, hostname=address,
                username=username, password=password)

    def get_fabric_ipinfo(self, filename, tftp_address):
        """ Send an IPMI get_fabric_ipinfo command to this target

        Note that this method puts the ip_info file on the TFTP server
        but does not retrieve it locally. """
        self._bmc.get_fabric_ipinfo(filename, tftp_address)

    def power_command(self, command):
        """ Send an IPMI power command to this target """
        self._bmc.handle.chassis_control(mode=command)

    def update_firmware(self, image_type, filename, tftp_address, slot_arg):
        """ Update firmware on this target. 
        
        Note that this only uploads to the first matching slot, and consists of
        3 steps: upload the image, wait for the transfer to finish, and
        activate the image on completion. """

        # Get all available slots
        results = self._bmc.get_firmware_info()[:-1]
        try:
            # Image type is an int
            slots = [x.slot for x in results[:-1] if
                    int(x.type.split()[0]) == int(image_type)]
        except ValueError:
            # Image type is a string
            slots = [x.slot for x in results[:-1] if
                    x.type.split()[1][1:-1] == image_type.upper()]

        # Select slots
        print len(slots)
        if slot_arg == "PRIMARY":
            if len(slots) < 1:
                raise ValueError("No primary slot found on host")
            slots = slots[:1]
        elif slot_arg == "SECONDARY":
            if len(slots) < 2:
                raise ValueError("No secondary slot found on host")
            slots = slots[1:2]
        elif slot_arg == "ALL":
            pass
        else:
            raise ValueError("Invalid slot argument")

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

            # Activate firmware on completion
            # TODO: consider raising an exception on failure
            if status == "Complete":
                self._bmc.activate_firmware(slot)

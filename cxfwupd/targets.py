#!/bin/env python

""" This class is a container of target Calxeda SoCs targeted for configuration
and provisioning. """

class targets:

    def __init__(self):
        # This is a mapping of group names to address sets
        self._groups = {}

    def get_settings_str(self):
        # TODO
        return 'None'

    def add_target_to_group(self, group, addr):
        """ Add the target address to a group """

        # Create group if it doesn't exist
        if not group in self._groups:
            self._groups[group] = set()

        # Add target to group
        self._groups[group].add(addr)

    def list_groups(self):
        """ Return a sorted list of the current groups """
        return sorted(self._groups.keys())

    def list_targets(self, group):
        """ Return a sorted list of targets in a group """
        return sorted(self._groups[group])

    def delete_group(self, group):
        """ Delete the specified target group """
        del self._groups[group]

    def group_exists(self, group):
        """ Returns true if the specified group exists """
        return group in self._groups

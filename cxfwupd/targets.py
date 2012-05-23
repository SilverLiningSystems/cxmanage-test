#!/bin/env python

""" This class is a container of target Calxeda SoCs targeted for configuration and
provisioning. """

class targets:

    def __init__(self):
        self.groups = {}

    def get_settings_str(self):
        # TODO
        return 'None'

    def add_target_to_group(self, group, addr):
        """ Add the address to the target group """
        
        # Create group if it doesn't exist
        if not group in self.groups:
            self.groups[group] = set()
        
        # Add target to group
        self.groups[group].add(addr)
    
    def list_groups(self):
        """ Return a sorted list of the currently stored groups """
        return sorted(self.groups.keys())
    
    def list_targets(self, group):
        """ Return a sorted list of addresses in a group """
        return sorted(self.groups[group])
    
    def delete_group(self, group):
        """ Delete the specified target group """
        del self.groups[group]

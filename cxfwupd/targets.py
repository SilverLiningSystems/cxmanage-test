#!/bin/env python

""" This class is a container of target Calxeda SoCs targeted for configuration and
provisioning. """

class targets:

    def __init__(self):
        targets = {}

    def get_settings_str(self):
        return 'None'

    def add_target(self, addr, metadata):
        """ Add the address and its associated metadata to the representation.
        Overwrite any existing data. """
        targets[addr] = metadata

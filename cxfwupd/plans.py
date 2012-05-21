#!/bin/env python

""" This class is a container for firmware distribution plans. """

class plans:

    def __init__(self):
        self._plans = {} # this will be a dictionary of tag: plan object

    def get_count_str(self):
        # FIXME
        return '0'

    def get_validate_status_str(self):
        # FIXME
        return 'No plans have been validated.'

    def get_executing_count_str(self):
        # FIXME
        return '0'

    def get_status_count_str(self):
        # FIXME
        return '0'

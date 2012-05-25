#!/bin/env python

""" This class is a container for firmware distribution plans. """

class Plans:

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

    def set_plan_command(self, plan, command):
        if not plan in self._plans:
            self._plans[plan] = Plan()
        self._plans[plan].set_command(command)

    def get_plan_command(self, plan):
        return self._plans[plan].get_command()

    def add_group_to_plan(self, plan, group):
        if not plan in self._plans:
            self._plans[plan] = Plan()
        self._plans[plan].add_group(group)

    def get_groups_from_plan(self, plan):
        return self._plans[plan].get_groups()

class Plan:
    def __init__(self):
        self._command = None
        self._groups = []

    def set_command(self, command):
        self._command = command

    def get_command(self):
        return self._command

    def add_group(self, group):
        self._groups.append(group)

    def del_group(self, group):
        if group in self._groups:
            del self._groups[group]

    def get_groups(self):
        return self._groups

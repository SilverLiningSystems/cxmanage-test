#!/bin/env python

""" This class provides the model for cxfwupd. It is a container for the
state of the firmware update tool.  Some objects it contains,
like tftp and targets, may be common to other Calxeda fabric configuration
tools. All object, including images, targets and plans may be externally
persisted. """

class model:

    def __init__(self, tftp, images, targets, plans):
        self._tftp = tftp
        self._images = images
        self._targets = targets
        self._plans = plans



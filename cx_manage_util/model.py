#!/bin/env python

""" This class provides the model for cxfwupd. It is a container for the
state of the firmware update tool.  Some objects it contains,
like tftp and targets, may be common to other Calxeda fabric configuration
tools. All object, including images, targets and plans may be externally
persisted. """

from tftp import Tftp
from images import Images
from targets import Targets
from plans import Plans

class Model:

    def __init__(self):
        self._tftp = Tftp()
        self._images = Images()
        self._targets = Targets()
        self._plans = Plans()



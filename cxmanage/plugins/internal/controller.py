#Copyright 2012 Calxeda, Inc.  All rights reserved.

from cxmanage import CxmanageError
from target import target_config_ecc

def controller_config_ecc(self, mode):
    """ Enable or disable ECC on all targets """
    successes = []
    errors = []
    for target in self.targets:
        try:
            target_config_ecc(target, mode)
            successes.append(target.address)
        except CxmanageError as e:
            errors.append("%s: %s" % (target.address, e))

    # Print successful hosts
    if len(successes) > 0:
        print "ECC set to \"%s\" for the following hosts:" % mode
        for host in successes:
            print host

    self._print_errors(errors)

    return len(errors) > 0

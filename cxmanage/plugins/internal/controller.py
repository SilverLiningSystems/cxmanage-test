#Copyright 2012 Calxeda, Inc.  All rights reserved.

from cxmanage import CxmanageError
from target import target_config_ecc, target_update_spiflash

def controller_update_spiflash(self, filename, skip_reset=False):
    """ Send firmware update commands to all targets in group. """

    # Update firmware on all targets
    successful_targets = []
    errors = []
    for target in self.targets:
        try:
            target_update_spiflash(target, self.work_dir,
                    self.tftp, filename)
            successful_targets.append(target)

        except CxmanageError as e:
            errors.append("%s: %s" % (target.address, e))

    # Reset MC upon completion
    # TODO: re-enable this once we know multi-node fabric can handle it
    """
    if not skip_reset:
        for target in successful_targets:
            target.mc_reset()
    """

    # Print successful hosts
    if len(successful_targets) > 0:
        print "Spi flash updated successfully on the following hosts:"
        for target in successful_targets:
            print target.address

    self._print_errors(errors)

    return len(errors) > 0

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

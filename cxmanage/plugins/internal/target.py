#Copyright 2012 Calxeda, Inc.  All rights reserved.

from cxmanage import CxmanageError

def target_config_ecc(self, mode):
    """ Set ECC mode on this target """
    try:
        # Get value
        if mode == "on":
            value = "01000000"
        elif mode == "off":
            value = "00000000"
        else:
            raise ValueError("\"%s\" is not a valid ECC mode" % mode)

        # Write to CDB and verify
        self.bmc.cdb_write(4, "02000002", value)
        result = self.bmc.cdb_read(4, "02000002")
        if not hasattr(result, "value") or result.value != value:
            raise CxmanageError("Failed to set ECC to \"%s\"" % mode)
    except IpmiError:
        raise CxmanageError("Failed to set ECC to \"%s\"" % mode)

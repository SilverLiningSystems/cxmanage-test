#Copyright 2012 Calxeda, Inc.  All rights reserved.

import os
import tempfile
import time

from cxmanage import CxmanageError

from pyipmi import IpmiError

def target_update_spiflash(self, work_dir, tftp, filename):
    """ Update spi_flash on this target. """
    contents = open(filename).read()

    self._vwrite(1, "Updating %s" % self.address)

    try:
        # Get slots
        try:
            slots = [x for x in self.bmc.get_firmware_info()
                    if hasattr(x, "slot")]
        except IpmiError:
            raise CxmanageError("Failed to retrieve firmware info")
        if not slots:
            raise CxmanageError("Failed to retrieve firmware info")

        # Update all slots
        for slot in slots:
            target_update_spiflash_slot(self, work_dir, tftp, contents, slot)
    finally:
        self._vwrite(1, "\n")

def target_update_spiflash_slot(self, work_dir, tftp, contents, slot):
    """ Update a single slot from spi_flash """

    # Get tftp address
    tftp_address = self._get_tftp_address(tftp)

    # Upload file to TFTP
    start = int(slot.offset, 16)
    end = start + int(slot.size, 16)
    filename = tempfile.mkstemp(".simg", work_dir + "/")[1]
    open(filename, "w").write(contents[start:end])
    basename = os.path.basename(filename)
    tftp.put_file(filename, basename)

    # Send firmware update command
    slot_id = int(slot.slot)
    image_type = slot.type.split()[1][1:-1]
    result = self.bmc.update_firmware(basename,
            slot_id, image_type, tftp_address)
    handle = result.tftp_handle_id

    # Extra wait for active CDB
    if image_type == "CDB":
        for a in range(9):
            time.sleep(1)
            self._vwrite(1, ".")

    # Wait for update to finish
    while True:
        time.sleep(1)
        self._vwrite(1, ".")
        result = self.bmc.get_firmware_status(handle)
        if not hasattr(result, "status"):
            raise CxmanageError("Unable to retrieve transfer info")
        if result.status != "In progress":
            break

    if result.status != "Complete":
        raise CxmanageError("Node reported transfer failure")

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

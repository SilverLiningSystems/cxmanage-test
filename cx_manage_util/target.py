""" Target objects used by the cx_manage_util controller """

import socket, time

from pyipmi import make_bmc, IpmiError
from pyipmi.bmc import LanBMC

class Target:
    """ Contains info for a single target. A target consists of a hostname,
    an username, and a password. """

    def __init__(self, address, username, password):
        self.address = address
        self.username = username
        self.password = password
        self.bmc = make_bmc(LanBMC, hostname=address,
                username=username, password=password)

    def get_fabric_ipinfo(self, tftp, filename):
        """ Send an IPMI get_fabric_ipinfo command to this target

        Note that this method puts the ip_info file on the TFTP server
        but does not retrieve it locally. """
        tftp_address = self._get_tftp_address(tftp)
        self.bmc.get_fabric_ipinfo(filename, tftp_address)

    def power_command(self, command):
        """ Send an IPMI power command to this target """
        try:
            self.bmc.handle.chassis_control(mode=command)
        except IpmiError:
            raise ValueError("Failed to send power command")

    def power_status(self):
        """ Return power status reported by IPMI """
        try:
            if self.bmc.handle.chassis_status().power_on:
                return "on"
            else:
                return "off"
        except IpmiError:
            raise ValueError("Failed to retrieve power status")

    def update_firmware(self, work_dir, tftp, images, slot_arg):
        """ Update firmware on this target. """
        # Get all updates
        plan = self._get_update_plan(images, slot_arg)
        for image, slot, new_version in plan:
            self._update_image(work_dir, tftp, image, slot, new_version)

    def mc_reset(self):
        """ Send an IPMI MC reset command to the target """
        try:
            self.bmc.mc_reset("cold")
        except IpmiError:
            raise ValueError("Failed to send MC reset command")

    def _get_tftp_address(self, tftp):
        """ Get the TFTP server address
        Returns a string in ip:port format """
        # Get address
        if tftp.is_internal() and tftp.get_address() == None:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect((self.address, 0))
            address = s.getsockname()[0]
            s.close()
        else:
            address = tftp.get_address()

        # Get port
        port = tftp.get_port()

        # Return in address:port form
        return "%s:%i" % (address, port)

    def _get_update_plan(self, images, slot_arg):
        """ Get an update plan.
        
        A plan consists of a list of tuples:
        (image, slot, version) """
        plan = []

        # Get all slots
        slots = self.bmc.get_firmware_info()[:-1]
        if not slots:
            raise ValueError("Failed to retrieve firmware info")

        soc_plan_made = False
        cdb_plan_made = False
        for image in images:        
            if image.type == "SPIF":
                # Add all slots
                for slot in slots:
                    plan.append((image, slot, 0))
            elif soc_plan_made and image.type == "CDB":
                for update in plan:
                    if update[0].type == "SOC_ELF":
                        plan.append((image, update[1].slot + 1, update[2]))
            elif cdb_plan_made and image.type == "SOC_ELF":
                for update in plan:
                    if update[0].type == "CDB":
                        plan.append((image, update[1].slot - 1, update[2]))
            else:
                # Filter slots for this type
                type_slots = [x for x in slots if
                        x.type.split()[1][1:-1] == image.type][:2]

                new_version = max([int(x.version, 16) for x in type_slots]) + 1

                if len(type_slots) < 1:
                    raise ValueError("No slots found on host")
                elif len(type_slots) < 2 or slot_arg == "FIRST":
                    plan.append((image, type_slots[0], new_version))
                elif slot_arg == "SECOND":
                    plan.append((image, type_slots[1], new_version))
                elif slot_arg == "BOTH":
                    # Add "oldest" slot first -- in other words, when updating
                    # both partitions, try to update the inactive one first.
                    if type_slots[0].version < type_slots[1].version:
                        plan.append((image, type_slots[0], new_version))
                        plan.append((image, type_slots[1], new_version))
                    else:
                        plan.append((image, type_slots[1], new_version))
                        plan.append((image, type_slots[0], new_version))
                elif slot_arg == "OLDEST":
                    # Choose second slot if both are the same version
                    if type_slots[0].version < type_slots[1].version:
                        plan.append((image, type_slots[0], new_version))
                    else:
                        plan.append((image, type_slots[1], new_version))
                elif slot_arg == "NEWEST":
                    # Choose first slot if both are the same version
                    if type_slots[0].version >= type_slots[1].version:
                        plan.append((image, type_slots[0], new_version))
                    else:
                        plan.append((image, type_slots[1], new_version))
                else:
                    raise ValueError("Invalid slot argument")

                if image.type == "SOC_ELF":
                    soc_plan_made = True
                elif image.type == "CDB_ELF":
                    cdb_plan_made = True

        return plan

    def _update_image(self, work_dir, tftp, image, slot, new_version):
        """ Update a single image. This includes uploading the image,
        performing the firmware update, crc32 check, and activation."""
        tftp_address = self._get_tftp_address(tftp)

        # Upload image to tftp server
        filename = image.upload(work_dir, tftp, slot, new_version)

        # Send firmware update command
        slot_id = int(slot.slot)
        image_type = image.type
        if image_type == "SPIF":
            image_type = slot.type.split()[1][1:-1]
        result = self.bmc.update_firmware(filename,
                slot_id, image_type, tftp_address)
        handle = result.tftp_handle_id

        if image_type == "CDB":
            time.sleep(9)

        # Wait for update to finish
        time.sleep(1)
        status = self.bmc.get_firmware_status(handle).status
        while status == "In progress":
            time.sleep(1)
            status = self.bmc.get_firmware_status(handle).status

        # Activate firmware on completion
        if status == "Complete":
            if image.type != "SPIF":
                # Verify crc
                if not self.bmc.check_firmware(slot_id).error:
                    # Activate
                    self.bmc.activate_firmware(slot_id)
                else:
                    raise ValueError("Node reported crc32 check failure")
        else:
            raise ValueError("Node reported transfer failure")

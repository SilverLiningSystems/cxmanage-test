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

    def update_firmware(self, work_dir, tftp, image, slot_arg):
        """ Update firmware on this target. """
        tftp_address = self._get_tftp_address(tftp)

        # Get all available slots
        slots = self._get_slots(image, slot_arg)

        for slot in slots:
            # Upload image to tftp server
            filename = image.upload(work_dir, tftp, slot)

            # Send firmware update command
            slot_id = int(slot.slot)
            image_type = image.type
            if image_type == "SPIF":
                image_type = slot.type.split()[1][1:-1]
            result = self.bmc.update_firmware(filename,
                    slot_id, image_type, tftp_address)
            handle = result.tftp_handle_id

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

    def _get_slots(self, image, slot_arg):
        """ Get a list of slots to update to """
        slots = self.bmc.get_firmware_info()[:-1]
        if not slots:
            raise ValueError("Failed to retrieve firmware info")

        if image.type == "SPIF":
            slots = slots[:1]
        else:
            try:
                # Image type is an int
                slots = [x for x in slots if
                        int(x.type.split()[0]) == int(image.type)]
            except ValueError:
                # Image type is a string
                slots = [x for x in slots if
                        x.type.split()[1][1:-1] == image.type.upper()]

            # Select slots
            if slot_arg == "PRIMARY":
                if len(slots) < 1:
                    raise ValueError("No primary slot found on host")
                slots = slots[:1]
            elif slot_arg == "SECONDARY":
                if len(slots) < 2:
                    raise ValueError("No secondary slot found on host")
                slots = slots[1:2]
            elif slot_arg == "ALL":
                pass
            else:
                raise ValueError("Invalid slot argument")

        return slots

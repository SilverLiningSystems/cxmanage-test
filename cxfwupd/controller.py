""" The controller object mediates between a UI and the application model.
In this case, the controller understands the model's container structure
and the objects it contains: tftp, images, targets and plans. """

import time

from model import model
from pyipmi import make_bmc, IpmiError
from pyipmi.bmc import LanBMC

class controller:

    def __init__(self, model):
        self._model = model

    def get_setting_report(self, subject):
        """ Various objects can have extended reports as well as
            status strings. """
        #FIXME
        return self.get_setting_str(subject)

    def get_setting_str(self, subject):
        """ Various objects in the model can report their status as a
        string.  This method invokes those reports for subjects it
        recognizes. """
        s = ''
        if subject == 'tftp':
            s = self._model._tftp.get_settings_str()
        elif subject == 'images':
            s = self._model._images.get_settings_str()
        elif subject == 'targets':
            s = self._model._targets.get_settings_str()
        elif subject == 'plans-cnt':
            s = self._model._plans.get_count_str()
        elif subject == 'plans-valid-cnt':
            s = self._model._plans.get_validate_status_str()
        elif subject == 'plans-exec-cnt':
            s = self._model._plans.get_executing_count_str()
        elif subject == 'plans-status-cnt':
            s = self._model._plans.get_status_count_str()
        else:
            s = "No report found."
        return s

    def get_status_code(self, subject):
        """ Various objects in the model have state that can be summarized
        in an integer code.  This method discovers and encodes those
        states. """
        code = -1
        if subject == 'tftp-selection':
            if not self._model._tftp.is_set():
                code = 0 # No tftp server set
            else:
                if self._model._tftp.is_internal():
                    code = 1
                else:
                    code = 2
        return code

###########################  TFTP-specific methods ###########################

    def set_internal_tftp_server(self, interface, port):
        """ Set up a TFTP server to be hosted locally """
        # TODO: may need to untrack images at this point
        self._model._tftp.set_internal_server(interface, port)

    def get_internal_tftp_interface(self):
        """ Return the interface used by the internal TFTP server"""
        return self._model._tftp.get_internal_server_interface()

    def get_internal_tftp_port(self):
        """ Return the port used by the internal TFTP server"""
        return self._model._tftp.get_port()

    def restart_tftp_server(self):
        """ Restart the TFTP server """
        self._model._tftp.restart_server()

    def set_external_tftp_server(self, addr, port):
        """ Set up a remote TFTP server """
        # TODO: may need to untrack images at this point
        self._model._tftp.set_external_server(addr, port)

    def get_external_tftp_addr(self):
        """ Return the address of the external TFTP server """
        return self._model._tftp.get_address()

    def get_external_tftp_port(self):
        """ Return the port used by the external TFTP server """
        return self._model._tftp.get_port()

    def tftp_get(self, tftppath, localpath):
        self._model._tftp.get_file(tftppath, localpath)

    def tftp_put(self, tftppath, localpath):
        self._model._tftp.put_file(tftppath, localpath)

###########################  Images-specific methods ###########################

    def list_images(self, subject):
        #FIXME
        return ''

    def validate_image_file(self, f):
        #FIXME
        return False

    def get_image_header_str(self, f):
        #FIXME
        return ''

    def add_image(self, image_type):
        pass

###########################  Targets-specific methods #########################

    def list_target_groups(self, subject):
        """ Return a formatted listing of target groups """
        #FIXME
        pass

    def add_targets_to_group(self, group, targets):
        """ Add the targets to the list of targets for the group.
        Eliminate duplicates."""
        for target in targets:
            self._model._targets.add_target_to_group(group, target)

    def delete_target_group(self, group):
        """ Delete the specified target group """
        self._model._targets.delete_group(group)

    def get_targets_in_range(self, startaddr, endaddr):
        """ Attempt to reach a socman on each of the addresses in the range.
        Return a list of socman addresses successfully reached. """

        addresses = []

        # Convert startaddr to int
        startaddr_bytes = map(int, startaddr.split("."))
        startaddr_i = ((startaddr_bytes[0] << 24) | (startaddr_bytes[1] << 16)
                | (startaddr_bytes[2] << 8) | (startaddr_bytes[3]))

        # Convert endaddr to int
        endaddr_bytes = map(int, endaddr.split("."))
        endaddr_i = ((endaddr_bytes[0] << 24) | (endaddr_bytes[1] << 16)
                | (endaddr_bytes[2] << 8) | endaddr_bytes[3])

        # Get ip addresses in range
        for i in range(startaddr_i, endaddr_i + 1):
            addr_bytes = [(i >> (24 - 8 * x)) & 0xff for x in range(4)]
            address = (str(addr_bytes[0]) + "." + str(addr_bytes[1]) + "." +
                    str(addr_bytes[2]) + "." + str(addr_bytes[3]))

            # TODO: attempt to reach socman at address
            # For now, just return all the addresses in range.
            addresses.append(address)

        return addresses

    def get_targets_from_fabric(self, nodeaddr):
        """ Attempt to get the addresses of socman instances that are known
        to the ipmi server at 'nodeaddr'.  If nodeaddr is a socman image,
        it will know about the instances that are part of fabric that
        nodeaddr\'s node belongs to.  Return a list of addresses reported."""
        addresses = []
        
        # Get TFTP address
        tftp_addr = self._model._tftp.get_address()
        tftp_addr += ":" + str(self._model._tftp.get_port())

        try:
            # Get ip_info file from fabric
            # TODO: username and password options?
            bmc = make_bmc(LanBMC, hostname=nodeaddr,
                    username="admin", password="admin")
            bmc.get_fabric_ipinfo("ip_info.txt", tftp_addr)
            time.sleep(1) # must delay before retrieving file
            self.tftp_get("ip_info.txt", "ip_info.txt")

            # Get addresses from ip_info file
            ip_info_file = open("ip_info.txt", "r")
            for line in ip_info_file:
                address = line.split()[-1]
                if address != "0.0.0.0":
                    addresses.append(address)
            ip_info_file.close()

        except IpmiError, IOError:
            # Unable to get IP list from ipmi.
            # Return empty list.
            pass

        return addresses

    def target_group_exists(self, grpname):
        """ Return true if the grpname is the name of a target group contained
        in the model."""
        return self._model._targets.group_exists(grpname)

 ########################    Plans-specific methods     ######################

    def list_plans(self, subject):
        """ Return a formatted list of plan names """
        #FIXME
        pass

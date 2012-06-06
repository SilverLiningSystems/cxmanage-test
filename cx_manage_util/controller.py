""" The controller object mediates between a UI and the application model.
In this case, the controller understands the model's container structure
and the objects it contains: tftp, images, targets and plans. """

import atexit
import shutil
import tempfile
import time

from cx_manage_util.image import Image
from cx_manage_util.target import Target
from cx_manage_util.tftp import Tftp

class Controller:
    """ The controller class serves as a manager for all the internals of
    cx_manage_util. Scripts or UIs can build on top of this to provide an user
    interface. """

    def __init__(self):
        self.tftp = Tftp()
        self.targets = []
        self.images = []
        self.work_dir = tempfile.mkdtemp(prefix="cxmanage-")
        atexit.register(self._cleanup)

    def _cleanup(self):
        """ Clean up temporary files """
        shutil.rmtree(self.work_dir)

###########################  TFTP-specific methods ###########################

    def set_internal_tftp_server(self, address=None, port=0):
        """ Set up a TFTP server to be hosted locally """
        self.tftp.set_internal_server(self.work_dir, address, port)

    def set_external_tftp_server(self, address, port=69):
        """ Set up a remote TFTP server """
        self.tftp.set_external_server(address, port)

###########################  Images-specific methods ##########################

    def add_image(self,
                  image_type,
                  filename,
                  version=None,
                  daddr=None,
                  force_simg=False,
                  skip_simg=False,
                  skip_crc32=False):
        """ Add an image to our collection """
        image = Image(image_type, filename, version, daddr,
                force_simg, skip_simg, skip_crc32)
        self.images.append(image)

###########################  Targets-specific methods #########################

    def add_target(self, address, username, password):
        """ Add the target to the list of targets for the group. """
        self.targets.append(Target(address, username, password))

    def get_targets_in_range(self, start, end):
        """ Return a list of addresses in the given IP range """
        try:
            # Convert startaddr to int
            start_bytes = map(int, start.split("."))
            start_i = ((start_bytes[0] << 24) | (start_bytes[1] << 16)
                    | (start_bytes[2] << 8) | (start_bytes[3]))

            # Convert endaddr to int
            end_bytes = map(int, end.split("."))
            end_i = ((end_bytes[0] << 24) | (end_bytes[1] << 16)
                    | (end_bytes[2] << 8) | (end_bytes[3]))

            # Get ip addresses in range
            addresses = []
            for i in range(start_i, end_i + 1):
                address_bytes = [(i >> (24 - 8 * x)) & 0xff for x in range(4)]
                address = (str(address_bytes[0]) + "." + str(address_bytes[1])
                        + "." + str(address_bytes[2]) + "."
                        + str(address_bytes[3]))

                addresses.append(address)

            return addresses

        except IndexError:
            raise ValueError

    def get_targets_from_fabric(self, address, username, password):
        """ Get a list of targets reported by fabric """

        # Create initial target
        target = Target(address, username, password)

        # Retrieve ip_info file
        target.get_fabric_ipinfo(self.tftp, "ip_info.txt")
        # TODO: don't sleep on failure.
        time.sleep(1) # must delay before retrieving file
        ip_info_path = self.work_dir + "/ip_info.txt"
        self.tftp.get_file("ip_info.txt", ip_info_path)

        # Parse addresses from ip_info file
        addresses = []
        ip_info_file = open(ip_info_path, "r")
        for line in ip_info_file:
            address = line.split()[-1]

            # TODO: question this -- is it necessary/proper?
            if address != "0.0.0.0":
                addresses.append(address)

        ip_info_file.close()

        return addresses

#########################    Execution methods    #########################

    def power_command(self, command):
        """ Send the given power command to all targets """
        successes = []
        errors = []
        for target in self.targets:
            try:
                target.power_command(command)
                successes.append(target.address)
            except Exception as e:
                errors.append("%s: %s" % (target.address, e))

        # Print successful hosts
        if len(successes) > 0:
            print "\nPower %s command executed successfully on the following hosts" % command
            for host in successes:
                print host

        # Print errors
        if len(errors) > 0:
            print "\nThe following errors occured"
            for error in errors:
                print error

    def power_status(self):
        """ Retrieve power status from all targets in group """
        results = []
        for target in self.targets:
            try:
                status = target.power_status()
                results.append("%s: %s" % (target.address, status))
            except Exception as e:
                results.append("%s: %s" % (target.address, e))

        # Print results
        if len(results) > 0:
            print "\nPower status"
            for result in results:
                print result
        else:
            print "\nERROR: Failed to retrieve power status info"

    def update_firmware(self, slot_arg, skip_reset=False):
        """ Send firmware update commands to all targets in group. """

        # Update firmware on all targets
        successes = []
        errors = []
        for target in self.targets:
            try:
                # Update each image
                reset_flag = False
                for image in self.images:
                    if image.type == "SOC_ELF":
                        reset_flag = True
                    target.update_firmware(self.work_dir, self.tftp, image, slot_arg)
                    successes.append(target.address)

                # Reset MC upon completion
                if reset_flag and not skip_reset:
                    target.mc_reset()

            except Exception as e:
                errors.append("%s: %s" % (target.address, e))

        # Print successful hosts
        if len(successes) > 0:
            print "\nFirmware updated successfully on the following hosts"
            for host in successes:
                print host

        # Print errors
        if len(errors) > 0:
            print "\nThe following errors occured"
            for error in errors:
                print error

    def mc_reset(self):
        """ Send the given power command to all targets """
        successes = []
        errors = []
        for target in self.targets:
            try:
                target.mc_reset()
                successes.append(target.address)
            except Exception as e:
                errors.append("%s: %s" % (target.address, e))

        # Print errors
        if len(errors) > 0:
            print "\nThe following errors occured"
            for error in errors:
                print error

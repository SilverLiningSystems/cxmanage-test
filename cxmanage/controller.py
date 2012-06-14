#Copyright 2012 Calxeda, Inc.  All Rights Reserved.

""" The controller object mediates between a UI and the application model.
In this case, the controller understands the model's container structure
and the objects it contains: tftp, images, and targets. """

import atexit
import os
import shutil
import tempfile
import time
import ConfigParser
import tarfile

from cxmanage.image import Image
from cxmanage.target import Target
from cxmanage.tftp import Tftp

class Controller:
    """ The controller class serves as a manager for all the internals of
    cxmanage. Scripts or UIs can build on top of this to provide an user
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
        if image_type == "PACKAGE":
            # Extract files and read config
            try:
                tarfile.open(filename, "r").extractall(self.work_dir)
            except (IOError, tarfile.ReadError):
                raise ValueError("%s is not a valid tar.gz package"
                        % os.path.basename(filename))
            if not os.path.exists(self.work_dir + "/MANIFEST"):
                raise ValueError("%s is not a valid firmware package"
                        % os.path.basename(filename))
            config = ConfigParser.SafeConfigParser()
            config.read(self.work_dir + "/MANIFEST")

            # Add all images from package
            for section in config.sections():
                filename = self.work_dir + "/" + section
                image_type = config.get(section, "type").upper()

                # Version
                if version == None and config.has_option(section, "version"):
                    image_version = config.getint(section, "version")
                else:
                    image_version = version
                # Daddr
                if daddr == None and config.has_option(section, "daddr"):
                    image_daddr = int(config.get(section, "daddr"), 16)
                else:
                    image_daddr = daddr
                # Force simg
                if (force_simg == False and
                        config.has_option(section, "force_simg")):
                    image_force_simg = config.getboolean(section, "force_simg")
                else:
                    image_force_simg = force_simg
                # Skip simg
                if (skip_simg == False and
                        config.has_option(section, "skip_simg")):
                    image_skip_simg = config.getboolean(section, "skip_simg")
                else:
                    image_skip_simg = skip_simg
                # Skip crc32
                if (skip_crc32 == False and
                        config.has_option(section, "skip_crc32")):
                    image_skip_crc32 = config.getboolean(section, "skip_crc32")
                else:
                    image_skip_crc32 = skip_crc32

                image = Image(image_type, filename, image_version, image_daddr,
                        image_force_simg, image_skip_simg, image_skip_crc32)
                self.images.append(image)

        else:
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

    def power(self, mode):
        """ Send the given power command to all targets """
        successes = []
        errors = []
        for target in self.targets:
            try:
                target.power(mode)
                successes.append(target.address)
            except Exception as e:
                errors.append("%s: %s" % (target.address, e))

        # Print successful hosts
        if len(successes) > 0:
            print ("\nPower %s command executed successfully on the following hosts:"
                    % mode)
            for host in successes:
                print host

        # Print errors
        if len(errors) > 0:
            print "\nThe following errors occured"
            for error in errors:
                print error

    def power_policy(self, state):
        """ Set the power policy for all targets """
        successes = []
        errors = []
        for target in self.targets:
            try:
                target.power_policy(state)
                successes.append(target.address)
            except Exception as e:
                errors.append("%s: %s" % (target.address, e))

        # Print successful hosts
        if len(successes) > 0:
            print ("\nPower policy set to \"%s\" for the following hosts:"
                    % state)
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

    def mc_reset(self):
        """ Send an MC reset command to all targets """
        errors = []
        for target in self.targets:
            try:
                target.mc_reset()
            except Exception as e:
                errors.append("%s: %s" % (target.address, e))

        # Print errors
        if len(errors) > 0:
            print "\nThe following errors occured"
            for error in errors:
                print error

    def update_firmware(self, slot_arg, skip_reset=False):
        """ Send firmware update commands to all targets in group. """

        # Update firmware on all targets
        successful_targets = []
        errors = []
        for target in self.targets:
            try:
                target.update_firmware(self.work_dir,
                        self.tftp, self.images, slot_arg)
                successful_targets.append(target)

            except Exception as e:
                errors.append("%s: %s" % (target.address, e))

        # Reset MC upon completion
        # TODO: re-enable this once we know multi-node fabric can handle it
        """
        should_reset = False
        for image in self.images:
            if image.type in ["SOC_ELF", "SPIF"]:
                should_reset = True
        if should_reset and not skip_reset:
            for target in successful_targets:
                target.mc_reset()
        """

        # Print successful hosts
        if len(successful_targets) > 0:
            print "\nFirmware updated successfully on the following hosts:"
            for target in successful_targets:
                print target.address

        # Print errors
        if len(errors) > 0:
            print "\nThe following errors occured"
            for error in errors:
                print error

    def set_ecc(self, mode):
        """ Enable or disable ECC on all targets """
        successes = []
        errors = []
        for target in self.targets:
            try:
                target.set_ecc(mode)
                successes.append(target.address)
            except Exception as e:
                errors.append("%s: %s" % (target.address, e))

        # Print successful hosts
        if len(successes) > 0:
            print "\nECC set to \"%s\" for the following hosts:" % mode
            for host in successes:
                print host

        # Print errors
        if len(errors) > 0:
            print "\nThe following errors occured"
            for error in errors:
                print error

    def get_sdr(self, name):
        """ Get SDR readings from all targets """
        results = []
        for target in self.targets:
            try:
                status = target.get_sdr(name)
                results.append("%s: %s" % (target.address, status))
            except Exception as e:
                results.append("%s: %s" % (target.address, e))

        # Print results
        if len(results) > 0:
            print "\nSDR readings for \"%s\"" % name
            for result in results:
                print result
        else:
            print "\nERROR: Failed to retrieve SDR info"

    def ipmitool_command(self, ipmitool_args):
        """ Run an arbitrary ipmitool command on all targets """
        errors = []
        for target in self.targets:
            try:
                target.ipmitool_command(ipmitool_args)
            except Exception as e:
                errors.append("%s: %s" % (target.address, e))

        # Print errors
        if len(errors) > 0:
            print "\nThe following errors occured"
            for error in errors:
                print error

#Copyright 2012 Calxeda, Inc.  All Rights Reserved.

""" The controller object mediates between a UI and the application model.
In this case, the controller understands the model's container structure
and the objects it contains: tftp, images, and targets. """

import atexit
import os
import shutil
import tempfile
import ConfigParser
import tarfile

from cxmanage import CxmanageError
from cxmanage.image import Image
from cxmanage.target import Target
from cxmanage.tftp import Tftp

class Controller:
    """ The controller class serves as a manager for all the internals of
    cxmanage. Scripts or UIs can build on top of this to provide an user
    interface. """

    def __init__(self, verbosity):
        self.tftp = Tftp()
        self.targets = []
        self.images = []
        self.work_dir = tempfile.mkdtemp(prefix="cxmanage-")
        atexit.register(self._cleanup)

        self.verbosity = verbosity

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
                  filename,
                  image_type,
                  simg=None,
                  version=None,
                  daddr=None,
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
                # SIMG
                if simg == None and config.has_option(section, "simg"):
                    image_simg = config.getboolean(section, "simg")
                else:
                    image_simg = simg
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
                # Skip crc32
                if (skip_crc32 == False and
                        config.has_option(section, "skip_crc32")):
                    image_skip_crc32 = config.getboolean(section, "skip_crc32")
                else:
                    image_skip_crc32 = skip_crc32

                image = Image(filename, image_type, image_simg,
                        image_version, image_daddr, image_skip_crc32)
                self.images.append(image)

        else:
            image = Image(filename, image_type, simg,
                    version, daddr, skip_crc32)
            self.images.append(image)

    def save_package(self, filename):
        """ Save all images as a firmware package """
        # Create the manifest
        config = ConfigParser.SafeConfigParser()
        for image in self.images:
            section = os.path.basename(image.filename)
            config.add_section(section)
            config.set(section, "type", image.type)
            config.set(section, "simg", str(image.simg))
            if image.version != None:
                config.set(section, "version", str(image.version))
            if image.daddr != None:
                config.set(section, "daddr", "%x" % image.daddr)
            if image.skip_crc32 != None:
                config.set(section, "skip_crc32", str(image.skip_crc32))
        manifest = open("%s/MANIFEST" % self.work_dir, "w")
        config.write(manifest)
        manifest.close()

        # Create the tar.gz package
        tar = tarfile.open(filename, "w")
        tar.add("%s/MANIFEST" % self.work_dir, "MANIFEST")
        for image in self.images:
            tar.add(image.filename, os.path.basename(image.filename))
        tar.close()

    def print_images(self):
        """ Print image info """
        for image in self.images:
            print "File: %s" % os.path.basename(image.filename)
            print "Type: %s" % image.type
            print "SIMG: %s" % image.simg
            if image.version != None:
                print "Version: %i" % image.version
            if image.daddr != None:
                print "Daddr: %x" % image.daddr
            print


###########################  Targets-specific methods #########################

    def add_target(self, address, username, password):
        """ Add the target to the list of targets for the group. """
        target = Target(address, username, password, self.verbosity)
        self.targets.append(target)

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
            raise ValueError("Invalid arguments to get_targets_in_range")

    def get_targets_from_fabric(self, address, username, password):
        """ Get a list of targets reported by fabric """

        # Create initial target
        target = Target(address, username, password, self.verbosity)

        # Retrieve ip_info file
        filename = "%s/ip_%s" % (self.work_dir, target.address)
        target.get_fabric_ipinfo(self.tftp, filename)

        # Parse addresses from ip_info file
        addresses = []
        for line in open(filename, "r"):
            address = line.split()[-1]

            # TODO: question this -- is it necessary/proper?
            if address != "0.0.0.0":
                addresses.append(address)

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
            except CxmanageError as e:
                errors.append("%s: %s" % (target.address, e))

        # Print successful hosts
        if len(successes) > 0:
            print ("Power %s command executed successfully on the following hosts:"
                    % mode)
            for host in successes:
                print host

        self._print_errors(errors)

        return len(errors) > 0

    def power_policy(self, state):
        """ Set the power policy for all targets """
        successes = []
        errors = []
        for target in self.targets:
            try:
                target.power_policy(state)
                successes.append(target.address)
            except CxmanageError as e:
                errors.append("%s: %s" % (target.address, e))

        # Print successful hosts
        if len(successes) > 0:
            print ("Power policy set to \"%s\" for the following hosts:"
                    % state)
            for host in successes:
                print host

        self._print_errors(errors)

        return len(errors) > 0

    def power_status(self):
        """ Retrieve power status from all targets in group """
        results = []
        errors = []
        for target in self.targets:
            try:
                status = target.power_status()
                results.append((target.address, status))
            except CxmanageError as e:
                errors.append("%s: %s" % (target.address, e))

        # Print results
        if len(results) > 0:
            print "Chassis power status"
            for result in results:
                print "%s: %s" % (result[0].ljust(16), result[1])

        self._print_errors(errors)

        return len(errors) > 0

    def mc_reset(self):
        """ Send an MC reset command to all targets """
        successes = []
        errors = []
        for target in self.targets:
            try:
                target.mc_reset()
                successes.append(target.address)
            except CxmanageError as e:
                errors.append("%s: %s" % (target.address, e))

        # Print successful hosts
        if len(successes) > 0:
            print "MC reset successfully on the following hosts:"
            for host in successes:
                print host

        self._print_errors(errors)

        return len(errors) > 0

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

            except CxmanageError as e:
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
            print "Firmware updated successfully on the following hosts:"
            for target in successful_targets:
                print target.address

        self._print_errors(errors)

        return len(errors) > 0

    def set_ecc(self, mode):
        """ Enable or disable ECC on all targets """
        successes = []
        errors = []
        for target in self.targets:
            try:
                target.set_ecc(mode)
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

    def get_sensor(self, name):
        """ Get sensor readings from all targets """
        results = []
        errors = []
        for target in self.targets:
            try:
                value = target.get_sensor(name)
                results.append((target.address, value))
            except CxmanageError as e:
                errors.append("%s: %s" % (target.address, e))

        if len(results) > 0:
            print "Sensor readings for \"%s\"" % name

            # Remove "(+/- 0)" from results
            results = [(x[0], x[1].replace("(+/- 0) ", "")) for x in results]

            try:
                # Get suffix
                suffix = " ".join(results[0][1].split()[1:])

                # Get values and average
                values = {}
                for result in results:
                    values[result] = float(result[1].split()[0])
                average = sum([values[x] for x in results]) / len(results)

                # Set new results
                results = [(x[0], "%.2f %s" % (values[x], suffix))
                        for x in results]
                results.append(("Average", "%.2f %s" % (average, suffix)))
            except ValueError:
                # Not all sensors returned numerical values, so just print
                # their output directly with no average
                pass

            # Print results
            for result in results:
                print "%s: %s" % (result[0].ljust(16), result[1])

        self._print_errors(errors)

        return len(errors) > 0

    def get_ipinfo(self):
        """ Get IP info from all targets """
        results = []
        errors = []
        for target in self.targets:
            try:
                filename = "%s/ip_%s" % (self.work_dir, target.address)
                target.get_fabric_ipinfo(self.tftp, filename)
                contents = open(filename).read().rstrip("\n")
                results.append("IP info from %s\n%s" % (target.address, contents))
            except CxmanageError as e:
                errors.append("%s: %s" % (target.address, e))

        for result in results:
            print result

        self._print_errors(errors)

        return len(errors) > 0

    def ipmitool_command(self, ipmitool_args):
        """ Run an arbitrary ipmitool command on all targets """
        errors = []
        for target in self.targets:
            try:
                target.ipmitool_command(ipmitool_args)
            except CxmanageError as e:
                errors.append("%s: %s" % (target.address, e))

        # Print errors
        self._print_errors(errors)

        return len(errors) > 0

    def _print_errors(self, errors):
        """ Print errors if they occured """
        if len(errors) > 0:
            print "The following errors occured"
            for error in errors:
                print error

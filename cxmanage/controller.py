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
from cxmanage.tftp import InternalTftp, ExternalTftp

class Controller:
    """ The controller class serves as a manager for all the internals of
    cxmanage. Scripts or UIs can build on top of this to provide an user
    interface. """

    def __init__(self, verbosity):
        self.tftp = None
        self.targets = []
        self.images = []
        self.verbosity = verbosity
        self.work_dir = tempfile.mkdtemp(prefix="cxmanage-")
        atexit.register(lambda: shutil.rmtree(self.work_dir))

###########################  TFTP-specific methods ###########################

    def set_internal_tftp_server(self, address=None, port=0):
        """ Set up a TFTP server to be hosted locally """
        # Kill the server if we can
        try:
            self.tftp.kill()
        except AttributeError:
            pass

        self.tftp = InternalTftp(address, port, self.verbosity)

    def set_external_tftp_server(self, address, port=69):
        """ Set up a remote TFTP server """
        # Kill the server if we can
        try:
            self.tftp.kill()
        except AttributeError:
            pass

        self.tftp = ExternalTftp(address, port, self.verbosity)

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

    def add_target(self, address, username, password, all_nodes=False):
        """ Add the target to the list of targets for the group. """
        # Do nothing if the target is already present
        for target in self.targets:
            if target.address == address:
                return

        target = Target(address, username, password, self.verbosity)
        if all_nodes:
            for address in target.get_ipinfo(self.work_dir, self.tftp):
                self.add_target(address, username, password)
        else:
            self.targets.append(target)

    def get_addresses_in_range(self, start, end):
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

    def power_policy_status(self):
        """ Get power policy status for all targets """
        results = []
        errors = []
        for target in self.targets:
            try:
                status = target.power_policy_status()
                results.append((target.address, status))
            except CxmanageError as e:
                errors.append("%s: %s" % (target.address, e))

        # Print results
        if len(results) > 0:
            print "Power policy status"
            for result in results:
                print "%s: %s" % (result[0].ljust(16), result[1])

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
        if not skip_reset:
            for image in self.images:
                if image.type == "SOC_ELF":
                    for target in successful_targets:
                        target.mc_reset()
                    break

        # Print successful hosts
        if len(successful_targets) > 0:
            print "Firmware updated successfully on the following hosts:"
            for target in successful_targets:
                print target.address

        self._print_errors(errors)

        return len(errors) > 0

    def get_sensors(self, name=None):
        """ Get sensor readings from all targets """
        sensor_names = []
        results = {}
        errors = []
        for target in self.targets:
            try:
                sensors = target.get_sensors()
                if name:
                    sensors = [x for x in sensors if x.sensor_name == name]
                for sensor in sensors:
                    if not sensor.sensor_name in sensor_names:
                        sensor_names.append(sensor.sensor_name)

                results[target.address] = sensors
            except CxmanageError as e:
                errors.append("%s: %s" % (target.address, e))

        if len(results) > 0:
            for sensor_name in sensor_names:
                print sensor_name

                average = 0.0
                for target in self.targets:
                    address = target.address

                    # Get sensor reading
                    sensor = [x for x in results[address]
                            if x.sensor_name == sensor_name][0]
                    reading = sensor.sensor_reading.replace("(+/- 0) ", "")

                    # Add to average and print
                    try:
                        value = float(reading.split()[0])
                        if average != None:
                            average += value
                            suffix = reading.lstrip("%f " % value)
                        print "%s: %.2f %s" % (address.ljust(16),
                                value, suffix)
                    except ValueError:
                        average = None
                        print "%s: %s" % (address.ljust(16), reading)
                if average != None:
                    average /= len(self.targets)

                # Print average
                if len(self.targets) > 1 and average != None:
                    print "%s: %.2f %s" % ("Average".ljust(16),
                            average, suffix)
                if sensor_name != sensor_names[-1]:
                    print

        self._print_errors(errors)

        return len(errors) > 0

    def get_ipinfo(self):
        """ Get IP info from all targets """
        results = []
        errors = []
        for target in self.targets:
            try:
                ipinfo = target.get_ipinfo(self.work_dir, self.tftp)
                results.append((target.address, ipinfo))
            except CxmanageError as e:
                errors.append("%s: %s" % (target.address, e))

        for result in results:
            address, ipinfo = result
            print "IP info from %s" % address
            for i in range(len(ipinfo)):
                print "Node %i: %s" % (i, ipinfo[i])
            if result != results[-1]:
                print

        self._print_errors(errors)

        return len(errors) > 0

    def config_reset(self):
        """ Send config reset command to all targets """
        successes = []
        errors = []
        for target in self.targets:
            try:
                target.config_reset()
                successes.append(target.address)
            except CxmanageError as e:
                errors.append("%s: %s" % (target.address, e))

        # Print successful hosts
        if len(successes) > 0:
            print "Configuration reset successfully on the following hosts:"
            for host in successes:
                print host

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

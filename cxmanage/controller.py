# Copyright (c) 2012, Calxeda Inc.
#
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
# * Redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer.
# * Redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution.
# * Neither the name of Calxeda Inc. nor the names of its contributors
# may be used to endorse or promote products derived from this software
# without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT HOLDERS OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS
# OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR
# TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF
# THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH
# DAMAGE.


""" The controller object mediates between a UI and the application model.
In this case, the controller understands the model's container structure
and the objects it contains: tftp, images, and targets. """

import atexit
import os
import shutil
import sys
import tempfile
import time
import ConfigParser
import tarfile

import pkg_resources

from cxmanage.command import Command
from cxmanage.image import Image
from cxmanage.target import Target
from cxmanage.tftp import InternalTftp, ExternalTftp
from cxmanage.ubootenv import UbootEnv

class Controller:
    """ The controller class serves as a manager for all the internals of
    cxmanage. Scripts or UIs can build on top of this to provide an user
    interface. """

    def __init__(self, verbosity=0, max_threads=1, image_class=Image,
            target_class=Target, retries=None, command_delay=0):
        if retries == None:
            retries = "prompt"
        self.tftp = None
        self.targets = []
        self.images = []
        self.verbosity = verbosity
        self.max_threads = max_threads
        self.command_delay = command_delay
        self.retries = retries
        self.target_class = target_class
        self.image_class = image_class
        self.firmware_version = None
        self.firmware_config = None
        self.required_socman_version = None
        self.work_dir = tempfile.mkdtemp(prefix="cxmanage-")
        atexit.register(self._cleanup)

    def _cleanup(self):
        """ Clean up working directory and tftp server """
        if os.path.exists(self.work_dir):
            shutil.rmtree(self.work_dir)

###########################  TFTP-specific methods ###########################

    def set_internal_tftp_server(self, address=None, port=0):
        """ Set up a TFTP server to be hosted locally """
        self.tftp = InternalTftp(address, port, self.verbosity)

    def set_external_tftp_server(self, address, port=69):
        """ Set up a remote TFTP server """
        self.tftp = ExternalTftp(address, port, self.verbosity)

###########################  Images-specific methods ##########################

    def add_image(self, filename, image_type, simg=None, priority=None,
            daddr=None, skip_crc32=False, version=None):
        """ Add an image to the controller """
        image = self.image_class(filename, image_type,
                simg, priority, daddr, skip_crc32, version)
        self.images.append(image)

    def add_package(self, filename, priority=None, skip_crc32=False,
            version=None):
        """ Add images from a firmware update package """
        # Extract files and read config
        try:
            tarfile.open(filename, "r").extractall(self.work_dir)
        except (IOError, tarfile.ReadError):
            raise ValueError("%s is not a valid tar.gz file"
                    % os.path.basename(filename))
        config = ConfigParser.SafeConfigParser()
        if len(config.read(self.work_dir + "/MANIFEST")) == 0:
            raise ValueError("%s is not a valid firmware package"
                    % os.path.basename(filename))

        if "package" in config.sections():
            cxmanage_ver = config.get("package", "required_cxmanage_version")
            try:
                pkg_resources.require("cxmanage>=%s" % cxmanage_ver)
            except pkg_resources.VersionConflict:
                raise ValueError("%s requires cxmanage version %s or later."
                        % (filename, cxmanage_ver))

            self.firmware_version = config.get("package", "firmware_version")
            self.firmware_config = config.get("package", "firmware_config")
            self.required_socman_version = config.get("package",
                    "required_socman_version")

        # Add all images from package
        image_sections = [x for x in config.sections() if x != "package"]
        for section in image_sections:
            filename = "%s/%s" % (self.work_dir, section)
            image_type = config.get(section, "type").upper()
            image_simg = None
            image_daddr = None
            image_priority = priority
            image_skip_crc32 = skip_crc32
            image_version = version

            # Read image options from config
            if config.has_option(section, "simg"):
                image_simg = config.getboolean(section, "simg")
            if priority == None and config.has_option(section, "priority"):
                image_priority = config.getint(section, "priority")
            if config.has_option(section, "daddr"):
                image_daddr = int(config.get(section, "daddr"), 16)
            if (skip_crc32 == False and
                    config.has_option(section, "skip_crc32")):
                image_skip_crc32 = config.getboolean(section, "skip_crc32")
            if version == None and config.has_option(section, "versionstr"):
                image_version = config.get(section, "versionstr")

            self.add_image(filename, image_type, image_simg, image_priority,
                    image_daddr, image_skip_crc32, image_version)

    def save_package(self, filename):
        """ Save all images as a firmware package """
        # Create the manifest
        config = ConfigParser.SafeConfigParser()
        for image in self.images:
            section = os.path.basename(image.filename)
            config.add_section(section)
            config.set(section, "type", image.type)
            config.set(section, "simg", str(image.simg))
            if image.priority != None:
                config.set(section, "priority", str(image.priority))
            if image.daddr != None:
                config.set(section, "daddr", "%x" % image.daddr)
            if image.skip_crc32:
                config.set(section, "skip_crc32", str(image.skip_crc32))
            if image.version != None:
                config.set(section, "versionstr", image.version)
        manifest = open("%s/MANIFEST" % self.work_dir, "w")
        config.write(manifest)
        manifest.close()

        # Create the tar.gz package
        if filename.endswith("gz"):
            tar = tarfile.open(filename, "w:gz")
        elif filename.endswith("bz2"):
            tar = tarfile.open(filename, "w:bz2")
        else:
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
            if image.priority != None:
                print "Priority: %i" % image.priority
            if image.daddr != None:
                print "Daddr: %x" % image.daddr
            if image.skip_crc32:
                print "Skip CRC32: %s" % image.skip_crc32
            if image.version != None:
                print "Version: %s" % image.version
            print


###########################  Targets-specific methods #########################

    def add_target(self, address, username, password):
        """ Add a target to the controller """
        for target in self.targets:
            if target.address == address:
                return

        target = self.target_class(address, username, password, self.verbosity)
        self.targets.append(target)

    def add_fabrics(self, addresses, username, password):
        """ Add all targets reported by each fabric """
        targets = [self.target_class(x, username, password, self.verbosity)
                for x in addresses]

        # Get IP info
        if self.verbosity >= 1:
            print "Getting IP addresses..."
        retries = self.retries
        if retries == "prompt":
            retries = 0
        results, errors = self._run_command_on_targets(targets, retries,
                "get_ipinfo", self.tftp)

        # Add all resulting targets
        for target in targets:
            if target.address in results:
                for ipinfo in results[target.address]:
                    self.add_target(ipinfo[1], username, password)

        # Print results and errors
        if self.verbosity >= 1 and len(self.targets) > 0:
            print "Discovered the following IP addresses:"
            for target in self.targets:
                print target.address
            print

        return len(errors) > 0

#########################    Execution methods    #########################

    def power(self, mode):
        """ Send the given power command to all targets """
        if self.verbosity >= 1:
            print "Sending power %s command..." % mode

        results, errors = self._run_command(True, "set_power", mode)

        if self.verbosity >= 1 and len(errors) == 0:
            print "Command completed successfully.\n"
        return len(errors) > 0


    def power_status(self):
        """ Retrieve power status from all targets in group """

        if self.verbosity >= 1:
            print "Getting power status..."
        results, errors = self._run_command(False, "get_power")

        # Print results
        if len(results) > 0:
            print "Power status"
            for target in self.targets:
                if target.address in results:
                    if results[target.address]:
                        result = "on"
                    else:
                        result = "off"
                    print "%s: %s" % (target.address.ljust(16), result)
            print

        if self.verbosity >= 1 and len(errors) > 0:
            print "Some errors occured during the command.\n"

        return len(errors) > 0

    def power_policy(self, mode):
        """ Set the power policy for all targets """
        if self.verbosity >= 1:
            print "Setting power policy to %s..." % mode

        results, errors = self._run_command(True, "set_power_policy", mode)

        if self.verbosity >= 1 and len(errors) == 0:
            print "Command completed successfully.\n"
        return len(errors) > 0

    def power_policy_status(self):
        """ Get power policy status for all targets """
        if self.verbosity >= 1:
            print "Getting power policy status..."
        results, errors = self._run_command(False, "get_power_policy")

        # Print results
        if len(results) > 0:
            print "Power policy status"
            for target in self.targets:
                if target.address in results:
                    print "%s: %s" % (target.address.ljust(16),
                            results[target.address])
            print

        if self.verbosity >= 1 and len(errors) > 0:
            print "Some errors occured during the command.\n"

        return len(errors) > 0

    def mc_reset(self):
        """ Send an MC reset command to all targets """
        if self.verbosity >= 1:
            print "Sending MC reset command..."

        results, errors = self._run_command(True, "mc_reset")

        if self.verbosity >= 1 and len(errors) == 0:
            print "Command completed successfully.\n"
        return len(errors) > 0

    def update_firmware(self, partition_arg="INACTIVE"):
        """ Send firmware update commands to all targets """
        if self.verbosity >= 1:
            print "Checking hosts..."

        results, errors = self._run_command(False, "check_firmware",
                self.required_socman_version, self.firmware_config)
        if errors:
            print "ERROR: Firmware update aborted."
            return True

        if self.verbosity >= 1:
            print "Updating firmware..."

        results, errors = self._run_command(True, "update_firmware", self.tftp,
                self.images, partition_arg, self.firmware_version)

        if self.verbosity >= 1 and len(errors) == 0:
            print "Command completed successfully.\n"
        return len(errors) > 0

    def firmware_info(self):
        """ Print firmware info for all targets """
        if self.verbosity >= 1:
            print "Getting firmware info..."
        results, errors = self._run_command(False, "get_firmware_info")

        for target in self.targets:
            if target.address in results:
                print "[ Firmware info for %s ]" % target.address

                for partition in results[target.address]:
                    print "Partition          : %s" % partition.partition
                    print "Type               : %s" % partition.type
                    print "Offset             : %s" % partition.offset
                    print "Size               : %s" % partition.size
                    print "Priority           : %s" % partition.priority
                    print "Daddr              : %s" % partition.daddr
                    print "Flags              : %s" % partition.flags
                    print "Version            : %s" % partition.version
                    print "In Use             : %s" % partition.in_use
                    print

        if self.verbosity >= 1 and len(errors) > 0:
            print "Some errors occured during the command.\n"

        return len(errors) > 0

    def get_sensors(self, name=""):
        """ Get sensor readings from all targets """
        if self.verbosity >= 1:
            print "Getting sensor readings..."
        results, errors = self._run_command(False, "get_sensors", name)

        if len(results) > 0:
            # Get sensor names
            sensor_names = []
            for address in results:
                for sensor in results[address]:
                    sensor_name = sensor.sensor_name
                    if not sensor_name in sensor_names:
                        sensor_names.append(sensor_name)

            # Print all sensors
            for sensor_name in sensor_names:
                print sensor_name

                count = 0
                average = 0.0
                for target in self.targets:
                    address = target.address
                    if address in results:
                        try:
                            sensor = [x for x in results[address]
                                    if x.sensor_name == sensor_name][0]
                            reading = sensor.sensor_reading.replace(
                                    "(+/- 0) ", "")

                            # Add to average and print
                            try:
                                value = float(reading.split()[0])
                                if average != None:
                                    count += 1
                                    average += value
                                    suffix = reading.lstrip("%f " % value)
                                print "%s: %.2f %s" % (address.ljust(16),
                                        value, suffix)
                            except ValueError:
                                average = None
                                print "%s: %s" % (address.ljust(16), reading)

                        except IndexError:
                            pass

                # Print average
                if count > 1 and average != None:
                    average /= count
                    print "%s: %.2f %s" % ("Average".ljust(16),
                            average, suffix)

                print

        if self.verbosity >= 1 and len(errors) > 0:
            print "Some errors occured during the command.\n"

        return len(errors) > 0

    def get_ipinfo(self):
        """ Get IP info from all targets """
        if self.verbosity >= 1:
            print "Getting IP info..."
        results, errors = self._run_command(False, "get_ipinfo", self.tftp)

        # Print results
        if len(results) > 0:
            for target in self.targets:
                if target.address in results:
                    print "IP info from %s" % target.address
                    ipinfo = results[target.address]
                    for entry in ipinfo:
                        print "Node %i: %s" % entry
                    print

        if self.verbosity >= 1 and len(errors) > 0:
            print "Some errors occured during the command.\n"

        return len(errors) > 0

    def get_macaddrs(self):
        """ Get mac addresses from all targets """
        if self.verbosity >= 1:
            print "Getting MAC addresses..."
        results, errors = self._run_command(False, "get_macaddrs", self.tftp)

        # Print results
        if len(results) > 0:
            for target in self.targets:
                if target.address in results:
                    print "MAC addresses from %s" % target.address
                    macaddrs = results[target.address]
                    for entry in macaddrs:
                        print "Node %i, Port %i: %s" % entry
                    print

        if self.verbosity >= 1 and len(errors) > 0:
            print "Some errors occured during the command.\n"

        return len(errors) > 0

    def config_reset(self):
        """ Send config reset command to all targets """
        if self.verbosity >= 1:
            print "Sending config reset command..."

        results, errors = self._run_command(True, "config_reset", self.tftp)

        if self.verbosity >= 1 and len(errors) == 0:
            print "Command completed successfully.\n"
        return len(errors) > 0

    def config_boot(self, boot_args):
        """ Send config boot command to all targets """

        # Make sure boot_args are valid
        try:
            UbootEnv().set_boot_order(boot_args)
        except ValueError as e:
            print e
            return True

        if self.verbosity >= 1:
            print "Setting boot order..."

        results, errors = self._run_command(True, "set_boot_order", self.tftp,
                boot_args)

        if self.verbosity >= 1 and len(errors) == 0:
            print "Command completed successfully.\n"
        return len(errors) > 0

    def config_boot_status(self):
        """ Get boot order from all targets """
        if self.verbosity >= 1:
            print "Getting boot orders..."
        results, errors = self._run_command(False, "get_boot_order", self.tftp)

        # Print results
        if len(results) > 0:
            print "Boot order"
            for target in self.targets:
                if target.address in results:
                    print "%s: %s" % (target.address.ljust(16),
                            ",".join(results[target.address]))
            print

        if self.verbosity >= 1 and len(errors) > 0:
            print "Some errors occured during the command.\n"

        return len(errors) > 0

    def info_basic(self):
        """ Get basic SoC info from all targets """
        if self.verbosity >= 1:
            print "Getting info..."
        results, errors = self._run_command(False, "info_basic")

        components = [
            ("soc_version", "Socman version"),
            ("cdb_version", "CDB version"),
            ("stage2_version", "Stage2boot version"),
            ("bootlog_version", "Bootlog version"),
            ("a9boot_version", "A9boot version"),
            ("uboot_version", "Uboot version"),
            ("ubootenv_version", "Ubootenv version")
        ]

        # Print results
        if len(results) > 0:
            for target in self.targets:
                if target.address in results:
                    result = results[target.address]
                    print "[ Info from %s ]" % target.address
                    print result.header
                    print "Firmware version   : %s" % result.version
                    for var, string in components:
                        if hasattr(result, var):
                            version = getattr(result, var)
                            print "%s: %s" % (string.ljust(19), version)
                    print

        if self.verbosity >= 1 and len(errors) > 0:
            print "Some errors occured during the command.\n"

        return len(errors) > 0

    def info_ubootenv(self):
        """ Print u-boot environment for all targets """
        if self.verbosity >= 1:
            print "Getting u-boot environments..."
        results, errors = self._run_command(False, "get_ubootenv", self.tftp)

        # Print results
        if len(results) > 0:
            for target in self.targets:
                if target.address in results:
                    ubootenv = results[target.address]
                    print "[ U-Boot Environment from %s ]" % target.address
                    for variable in ubootenv.variables:
                        print "%s=%s" % (variable, ubootenv.variables[variable])
                    print

        if self.verbosity >= 1 and len(errors) > 0:
            print "Some errors occured during the command.\n"

        return len(errors) > 0

    def info_dump(self):
        """ Dump info from all targets """
        if self.verbosity >= 1:
            print "Getting all info..."
        results, errors = self._run_command(False, "info_dump", self.tftp)

        # Print results
        if len(results) > 0:
            for target in self.targets:
                if target.address in results:
                    print "[ Info dump from %s ]" % target.address
                    print results[target.address]
                    print

        if self.verbosity >= 1 and len(errors) > 0:
            print "Some errors occured during the command.\n"

        return len(errors) > 0

    def ipmitool_command(self, ipmitool_args):
        """ Run an arbitrary ipmitool command on all targets """
        if self.verbosity >= 1:
            print "Running IPMItool command..."
        results, errors = self._run_command(True, "ipmitool_command",
                ipmitool_args)

        # Print results
        if len(results) > 0:
            for target in self.targets:
                if target.address in results and results[target.address] != "":
                    print "[ IPMItool output from %s ]" % target.address
                    print results[target.address]
                    print

        if self.verbosity >= 1 and len(errors) > 0:
            print "Some errors occured during the command.\n"

        return len(errors) > 0

    def _run_command(self, retry_prompt, name, *args):
        """ Run a command on all targets """
        retries = self.retries
        if retries == "prompt" and not retry_prompt:
            retries = 0
        return self._run_command_on_targets(self.targets, retries, name, *args)

    def _run_command_on_targets(self, targets, retries, name, *args):
        """ Run a multi-threaded command on the specified targets.

        Returns (results, errors) which map addresses to their results """

        command = Command(targets, name, args, self.command_delay,
                self.max_threads)
        command.start()

        try:
            counter = 0
            while command.is_alive():
                if self.verbosity == 1:
                    self._print_command_status(targets, command, counter)
                    counter += 1
                time.sleep(0.25)

            results = command.results
            errors = command.errors
        except KeyboardInterrupt:
            retries = 0
            results = command.results.copy()
            errors = command.errors.copy()
            for target in targets:
                if not (target.address in results or target.address in errors):
                    errors[target.address] = "Aborted by keyboard interrupt"

        if self.verbosity == 1:
            self._print_command_status(targets, command, counter)
            print "\n"

        # Handle errors
        should_retry = False
        if len(errors) > 0:
            self._print_errors(targets, errors)
            if retries == "prompt":
                sys.stdout.write("Retry command on failed hosts? (y/n): ")
                sys.stdout.flush()
                while True:
                    command = raw_input().strip().lower()
                    if command in ['y', 'yes']:
                        should_retry = True
                        break
                    elif command in ['n', 'no']:
                        print
                        break
            elif retries >= 1:
                should_retry = True
                if retries == 1:
                    print "Retrying command 1 more time..."
                elif retries > 1:
                    print "Retrying command %i more times..." % retries
                retries -= 1
        if should_retry:
            targets = [x for x in targets if x.address in errors]
            new_results, errors = self._run_command_on_targets(targets,
                    retries, name, *args)
            results.update(new_results)

        return results, errors

    def _print_errors(self, targets, errors):
        """ Print errors if they occured """
        if len(errors) > 0:
            print "Command failed on these hosts"
            for target in targets:
                if target.address in errors:
                    print "%s: %s" % (target.address.ljust(16),
                            errors[target.address])
            print

    def _print_command_status(self, targets, command, counter):
        """ Print the status of a command """
        message = "\r%i successes  |  %i errors  |  %i nodes left  |  %s"
        successes = len(command.results)
        errors = len(command.errors)
        nodes_left = len(targets) - successes - errors
        dots = "".join(["." for x in range(counter % 4)]).ljust(3)
        sys.stdout.write(message % (successes, errors, nodes_left, dots))
        sys.stdout.flush()

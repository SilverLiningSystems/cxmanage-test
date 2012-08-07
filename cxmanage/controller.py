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
import tempfile
import threading
import time
import ConfigParser
import tarfile

from cxmanage.image import Image
from cxmanage.target import Target
from cxmanage.tftp import InternalTftp, ExternalTftp
from cxmanage.indicator import Indicator
from cxmanage.ubootenv import UbootEnv

class Controller:
    """ The controller class serves as a manager for all the internals of
    cxmanage. Scripts or UIs can build on top of this to provide an user
    interface. """

    def __init__(self, verbosity=0, max_threads=1,
            image_class=Image, target_class=Target):
        self.tftp = None
        self.targets = []
        self.images = []
        self.verbosity = verbosity
        self.max_threads = max_threads
        self.target_class = target_class
        self.image_class = image_class
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

    def add_image(self, filename, image_type, simg=None,
            version=None, daddr=None, skip_crc32=False):
        """ Add an image to our collection """
        if image_type == "PACKAGE":
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

            # Add all images from package
            for section in config.sections():
                filename = "%s/%s" % (self.work_dir, section)
                image_type = config.get(section, "type").upper()
                image_simg = simg
                image_version = version
                image_daddr = daddr
                image_skip_crc32 = skip_crc32

                # Read image options from config
                if simg == None and config.has_option(section, "simg"):
                    image_simg = config.getboolean(section, "simg")
                if version == None and config.has_option(section, "version"):
                    image_version = config.getint(section, "version")
                if daddr == None and config.has_option(section, "daddr"):
                    image_daddr = int(config.get(section, "daddr"), 16)
                if (skip_crc32 == False and
                        config.has_option(section, "skip_crc32")):
                    image_skip_crc32 = config.getboolean(section, "skip_crc32")

                image = self.image_class(filename, image_type, image_simg,
                        image_version, image_daddr, image_skip_crc32)
                self.images.append(image)

        else:
            image = self.image_class(filename, image_type,
                    simg, version, daddr, skip_crc32)
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

        target = self.target_class(address, username, password, self.verbosity)
        if all_nodes:
            for entry in target.get_ipinfo(self.tftp):
                self.add_target(entry[1], username, password)
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
                addresses.append("%i.%i.%i.%i" % tuple(address_bytes))

            return addresses

        except IndexError:
            raise ValueError("Invalid arguments to get_targets_in_range")

#########################    Execution methods    #########################

    def power(self, mode):
        """ Send the given power command to all targets """

        if self.verbosity >= 1:
            print "Sending power %s command to these hosts:" % mode
            for target in self.targets:
                print target.address
            print

        results, errors = self._run_command("set_power", mode)

        if self.verbosity >= 1 and len(errors) == 0:
            print "Command completed successfully.\n"
        self._print_errors(errors)

        return len(errors) > 0

    def power_status(self):
        """ Retrieve power status from all targets in group """

        results, errors = self._run_command("get_power")

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

        # Print errors
        self._print_errors(errors)

        return len(errors) > 0

    def power_policy(self, mode):
        """ Set the power policy for all targets """

        if self.verbosity >= 1:
            print "Setting power policy on these hosts:"
            for target in self.targets:
                print target.address
            print

        results, errors = self._run_command("set_power_policy", mode)

        if self.verbosity >= 1 and len(errors) == 0:
            print "Command completed successfully.\n"
        self._print_errors(errors)

        return len(errors) > 0

    def power_policy_status(self):
        """ Get power policy status for all targets """
        results, errors = self._run_command("get_power_policy")

        # Print results
        if len(results) > 0:
            print "Power policy status"
            for target in self.targets:
                if target.address in results:
                    print "%s: %s" % (target.address.ljust(16),
                            results[target.address])
            print

        # Print errors
        self._print_errors(errors)

        return len(errors) > 0

    def mc_reset(self):
        """ Send an MC reset command to all targets """

        if self.verbosity >= 1:
            print "Sending MC reset command to these hosts:"
            for target in self.targets:
                print target.address
            print

        results, errors = self._run_command("mc_reset")

        if self.verbosity >= 1 and len(errors) == 0:
            print "Command completed successfully.\n"
        self._print_errors(errors)

        return len(errors) > 0

    def update_firmware(self, slot_arg="INACTIVE"):
        """ Send firmware update commands to all targets in group. """

        if self.verbosity >= 1:
            print "Updating firmware on these hosts:"
            for target in self.targets:
                print target.address
            print

        # Get results and errors
        results, errors = self._run_command("update_firmware",
                self.tftp, self.images, slot_arg)

        if self.verbosity >= 1 and len(errors) == 0:
            print "Command completed successfully.\n"
        self._print_errors(errors)

        return len(errors) > 0

    def get_sensors(self, name=None):
        """ Get sensor readings from all targets """
        results, errors = self._run_command("get_sensors")

        if len(results) > 0:
            # Get sensor names
            sensor_names = []
            for address in results:
                for sensor in results[address]:
                    if (name in [None, sensor.sensor_name] and not
                            sensor.sensor_name in sensor_names):
                        sensor_names.append(sensor.sensor_name)

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

        self._print_errors(errors)

        return len(errors) > 0

    def get_ipinfo(self):
        """ Get IP info from all targets """
        results, errors = self._run_command("get_ipinfo", self.tftp)

        # Print results
        if len(results) > 0:
            for target in self.targets:
                if target.address in results:
                    print "IP info from %s" % target.address
                    ipinfo = results[target.address]
                    for entry in ipinfo:
                        print "Node %i: %s" % entry
                    print

        self._print_errors(errors)

        return len(errors) > 0

    def get_macaddrs(self):
        """ Get mac addresses from all targets """
        results, errors = self._run_command("get_macaddrs", self.tftp)

        # Print results
        if len(results) > 0:
            for target in self.targets:
                if target.address in results:
                    print "Mac addresses from %s" % target.address
                    macaddrs = results[target.address]
                    for entry in macaddrs:
                        print "Node %i, Port %i: %s" % entry
                    if target != self.targets[-1] or len(errors) > 0:
                        print

        self._print_errors(errors)

        return len(errors) > 0

    def config_reset(self):
        """ Send config reset command to all targets """

        if self.verbosity >= 1:
            print "Resetting configuration on these hosts:"
            for target in self.targets:
                print target.address
            print

        results, errors = self._run_command("config_reset", self.tftp)

        if self.verbosity >= 1 and len(errors) == 0:
            print "Command completed successfully.\n"
        self._print_errors(errors)

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
            print "Setting boot order on these hosts:"
            for target in self.targets:
                print target.address
            print

        results, errors = self._run_command("set_boot_order",
                self.tftp, boot_args)

        if self.verbosity >= 1 and len(errors) == 0:
            print "Command completed successfully.\n"
        self._print_errors(errors)

        return len(errors) > 0

    def config_boot_status(self):
        """ Get boot order from all targets """
        results, errors = self._run_command("get_boot_order", self.tftp)

        # Print results
        if len(results) > 0:
            print "Boot order"
            for target in self.targets:
                if target.address in results:
                    print "%s: %s" % (target.address.ljust(16),
                            ",".join(results[target.address]))
            print

        # Print errors
        self._print_errors(errors)

        return len(errors) > 0

    def info_basic(self):
        """ Get basic SoC info from all targets """
        results, errors = self._run_command("info_basic")

        # Print results
        if len(results) > 0:
            for target in self.targets:
                if target.address in results:
                    result = results[target.address]
                    print "[ Info from %s ]" % target.address
                    print result.header
                    print "  Version: %s" % result.version
                    print "  Build Number: %s" % result.build_number
                    print "  Timestamp (%s): %s" % (result.timestamp,
                            time.ctime(int(result.timestamp)))
                    print

        # Print errors
        self._print_errors(errors)

        return len(errors) > 0

    def info_ubootenv(self):
        """ Print u-boot environment for all targets """
        results, errors = self._run_command("get_ubootenv", self.tftp)

        # Print results
        if len(results) > 0:
            for target in self.targets:
                if target.address in results:
                    ubootenv = results[target.address]
                    print "[ U-Boot Environment from %s ]" % target.address
                    for variable in ubootenv.variables:
                        print "%s=%s" % (variable, ubootenv.variables[variable])
                    print

        # Print errors
        self._print_errors(errors)

        return len(errors) > 0

    def info_dump(self):
        """ Dump info from all targets """
        for target in self.targets:
            print "[ Info dump from %s ]" % target.address
            target.info_dump(self.tftp)

        return False

    def ipmitool_command(self, ipmitool_args):
        """ Run an arbitrary ipmitool command on all targets """
        results, errors = self._run_command("ipmitool_command", ipmitool_args)

        # Print results
        if len(results) > 0:
            for target in self.targets:
                if target.address in results and results[target.address] != "":
                    print "[ IPMItool output from %s ]" % target.address
                    print results[target.address]
                    print

        # Print errors
        self._print_errors(errors)

        return len(errors) > 0

    def _run_command(self, name, *args):
        """ Run a target command with multiple threads

        Returns (results, errors) which map addresses to their results """

        threads = set()

        results = {}
        errors = {}

        # Start indicator
        indicator = Indicator(self.targets, results, errors)
        if self.verbosity == 1:
            indicator.start()

        for target in self.targets:
            # Wait while we have too many running threads
            while len(threads) >= self.max_threads:
                time.sleep(0.001)
                for thread in threads:
                    if not thread.is_alive():
                        threads.remove(thread)
                        if thread.error == None:
                            results[thread.target.address] = thread.result
                        else:
                            errors[thread.target.address] = thread.error
                        break

            # Start the new thread
            thread = ControllerCommandThread(target, name, args)
            thread.start()
            threads.add(thread)

        # Join with any remaining threads
        while len(threads) > 0:
            time.sleep(0.001)
            for thread in threads:
                if not thread.is_alive():
                    threads.remove(thread)
                    if thread.error == None:
                        results[thread.target.address] = thread.result
                    else:
                        errors[thread.target.address] = thread.error
                    break

        # Stop indicator
        if self.verbosity == 1:
            indicator.stop()
            print "\n"

        return results, errors

    def _print_errors(self, errors):
        """ Print errors if they occured """
        if len(errors) > 0:
            print "Command failed on these hosts"
            for target in self.targets:
                if target.address in errors:
                    print "%s: %s" % (target.address.ljust(16),
                            errors[target.address])
            print

class ControllerCommandThread(threading.Thread):
    """ Thread for executing a command on a target """

    def __init__(self, target, name, args):
        threading.Thread.__init__(self)
        self.daemon = True

        self.target = target
        self.function = getattr(target, name)
        self.args = args
        self.result = None
        self.error = None

    def run(self):
        try:
            self.result = self.function(*self.args)
        except Exception as e:
            self.error = e

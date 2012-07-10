#Copyright 2012 Calxeda, Inc.  All Rights Reserved.

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
        atexit.register(self.kill)

    def kill(self):
        """ Clean up working directory and tftp server """
        if os.path.exists(self.work_dir):
            shutil.rmtree(self.work_dir)
        if self.tftp != None:
            self.tftp.kill()

###########################  TFTP-specific methods ###########################

    def set_internal_tftp_server(self, address=None, port=0):
        """ Set up a TFTP server to be hosted locally """
        # Kill the server if we can
        if self.tftp != None:
            self.tftp.kill()

        self.tftp = InternalTftp(address, port, self.verbosity)

    def set_external_tftp_server(self, address, port=69):
        """ Set up a remote TFTP server """
        # Kill the server if we can
        if self.tftp != None:
            self.tftp.kill()

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

                image = self.image_class(filename, image_type, image_simg,
                        image_version, image_daddr, image_skip_crc32)
                self.images.append(image)

        else:
            image = self.image_class(filename, image_type, simg,
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
            for entry in target.get_ipinfo(self.work_dir, self.tftp):
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
        results, errors = self._run_command("power", mode)

        # Print successful addresses
        if self.verbosity >= 1 and len(results) > 0:
            print ("Power %s command executed successfully on the following hosts:"
                    % mode)
            for target in self.targets:
                if target.address in results:
                    print target.address
            print

        self._print_errors(errors)

        return len(errors) > 0

    def power_status(self):
        """ Retrieve power status from all targets in group """
        results, errors = self._run_command("power_status")

        # Print results
        if len(results) > 0:
            print "Chassis power status"
            for target in self.targets:
                if target.address in results:
                    print "%s: %s" % (target.address.ljust(16),
                            results[target.address])
            print

        # Print errors
        self._print_errors(errors)

        return len(errors) > 0

    def power_policy(self, mode):
        """ Set the power policy for all targets """
        results, errors = self._run_command("power_policy", mode)

        # Print successful addresses
        if self.verbosity >= 1 and len(results) > 0:
            print ("Power policy set to \"%s\" for the following hosts:"
                    % mode)
            for target in self.targets:
                if target.address in results:
                    print target.address
            print

        self._print_errors(errors)

        return len(errors) > 0

    def power_policy_status(self):
        """ Get power policy status for all targets """
        results, errors = self._run_command("power_policy_status")

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
        results, errors = self._run_command("mc_reset")

        # Print successful addresses
        if self.verbosity >= 1 and len(results) > 0:
            print "MC reset successfully on the following hosts:"
            for target in self.targets:
                if target.address in results:
                    print target.address
            print

        self._print_errors(errors)

        return len(errors) > 0

    def update_firmware(self, slot_arg="INACTIVE", skip_reset=False):
        """ Send firmware update commands to all targets in group. """
        # Start a progress indicator
        indicator = Indicator("Updating")
        if self.verbosity == 1:
            indicator.start()

        # Get results and errors
        results, errors = self._run_command("update_firmware",
                self.work_dir, self.tftp, self.images, slot_arg)

        # Reset MC upon completion
        if not skip_reset:
            for image in self.images:
                if image.type == "SOC_ELF":
                    self._run_command("mc_reset")
                    break

        # Signal indicator to stop
        indicator.stop()

        # Print successful addresses
        if self.verbosity >= 1 and len(results) > 0:
            print "Firmware updated successfully on the following hosts:"
            for target in self.targets:
                if target.address in results:
                    print target.address
            print

        self._print_errors(errors)

        return len(errors) > 0

    def get_sensors(self, name=None):
        """ Get sensor readings from all targets """
        results, errors = self._run_command("get_sensors")

        if len(results) > 0:
            sensors = {}
            sensor_names = []
            for target in self.targets:
                for sensor in results.get(target.address, []):
                    sensor_name = sensor.sensor_name
                    reading = sensor.sensor_reading.replace("(+/- 0) ", "")
                    if name in [None, sensor_name]:
                        if not sensor_name in sensors:
                            sensors[sensor_name] = {}
                            sensor_names.append(sensor_name)
                        sensors[sensor_name][target.address] = reading

            for sensor_name in sensor_names:
                print sensor_name

                average = 0.0
                for target in self.targets:
                    address = target.address
                    if address in sensors[sensor_name]:
                        reading = sensors[sensor_name][address]

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

                # Print average
                if len(self.targets) > 1 and average != None:
                    average /= len(self.targets)
                    print "%s: %.2f %s" % ("Average".ljust(16),
                            average, suffix)

                print

        self._print_errors(errors)

        return len(errors) > 0

    def get_ipinfo(self):
        """ Get IP info from all targets """
        results, errors = self._run_command("get_ipinfo",
                self.work_dir, self.tftp)

        # Print results
        if len(results) > 0:
            for target in self.targets:
                if target.address in results:
                    print "IP info from %s" % target.address
                    ipinfo = results[target.address]
                    for i in range(len(ipinfo)):
                        print "Node %i: %s" % ipinfo[i]
                    print

        self._print_errors(errors)

        return len(errors) > 0

    def get_macaddrs(self):
        """ Get mac addresses from all targets """
        results, errors = self._run_command("get_macaddrs",
                self.work_dir, self.tftp)

        # Print results
        if len(results) > 0:
            for target in self.targets:
                if target.address in results:
                    print "Mac addresses from %s" % target.address
                    macaddrs = results[target.address]
                    for i in range(len(macaddrs)):
                        print "Node %i, Port %i: %s" % macaddrs[i]
                    print

        self._print_errors(errors)

        return len(errors) > 0

    def config_reset(self):
        """ Send config reset command to all targets """
        results, errors = self._run_command("config_reset",
            self.work_dir, self.tftp)

        # Print successful addresses
        if self.verbosity >= 1 and len(results) > 0:
            print "Configuration reset successfully on the following hosts:"
            for target in self.targets:
                if target.address in results:
                    print target.address
            print

        self._print_errors(errors)

        return len(errors) > 0

    def config_boot(self, boot_args):
        """ Send config boot command to all targets """
        results, errors = self._run_command("config_boot",
                self.work_dir, self.tftp, boot_args)

        # Print successful addresses
        if self.verbosity >= 1 and len(results) > 0:
            print "Boot order changed successfully on the following hosts:"
            for target in self.targets:
                if target.address in results:
                    print target.address
            print

        self._print_errors(errors)

        return len(errors) > 0

    def config_boot_status(self):
        """ Get boot order from all targets """
        results, errors = self._run_command("config_boot_status",
                self.work_dir, self.tftp)

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

    def ipmitool_command(self, ipmitool_args):
        """ Run an arbitrary ipmitool command on all targets """
        results, errors = self._run_command("ipmitool_command", ipmitool_args)

        # Print errors
        self._print_errors(errors)

        return len(errors) > 0

    def _run_command(self, name, *args):
        """ Run a target command with multiple threads

        Returns a mapping of addresses to a (results, errors) tuple """

        threads = [ControllerCommandThread(target, name, args)
                for target in self.targets]
        running_threads = set()

        for thread in threads:
            # Wait while we have too many running threads
            while len(running_threads) >= self.max_threads:
                time.sleep(0.001)
                for running_thread in running_threads:
                    if not running_thread.is_alive():
                        running_threads.remove(running_thread)
                        break

            # Start the thread
            thread.start()
            running_threads.add(thread)

        # Join with any remaining threads
        for thread in running_threads:
            thread.join()

        # Get results and errors
        results = {}
        errors = {}
        for thread in threads:
            if thread.error != None:
                errors[thread.target.address] = thread.error
            else:
                results[thread.target.address] = thread.result

        return results, errors

    def _print_errors(self, errors):
        """ Print errors if they occured """
        if len(errors) > 0:
            print "The following errors occured"
            for target in self.targets:
                if target.address in errors:
                    print "%s: %s" % (target.address.ljust(16),
                            errors[target.address])
            print

class ControllerCommandThread(threading.Thread):
    def __init__(self, target, name, args):
        threading.Thread.__init__(self)
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

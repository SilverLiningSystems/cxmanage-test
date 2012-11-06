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


"""Python implementation of a single node. A node represents a single
Calxeda ECME (Energy CoreManagement Engine).
"""


import os
import time
import shutil
import atexit
import tempfile
import traceback
import subprocess

from image import Image
from pyipmi import make_bmc, IpmiError
from infodump import get_info_dump
from ubootenv import UbootEnv
from pyipmi.bmc import LanBMC
from pkg_resources import parse_version
from tftpy.TftpShared import TftpException

from cx_exceptions import NoIpInfoError, TimeoutError, NoMacAddressError 
from cx_exceptions import NoSensorError, NoFirmwareInfoError, SocmanVersionError
from cx_exceptions import FirmwareConfigError, PriorityIncrementError
from cx_exceptions import NoPartitionError, TransferFailure, ImageSizeError


class Node(object):
    """The node represents a single node which is defined as an:
    ip_address, and login credentials, to facilitate communications between
    Python -> Calxeda ECMEs.
    """

    def __init__(self, ip_address, username="admin", password="admin", 
                  verbose=False):
        """Default constructor for the Node class.
        
        :param ip_address: The ip_address of the Node.
        :type ip_address: string
        :param username: The login username credential. [Default admin]
        :type username: string
        :param password: The login password credential. [Default admin]
        :type password: string
        :param verbose: Flag to turn on verbose output (cmd/response).
        :type verbose: boolean
        """
        self.ip_address = ip_address
        self.username = username
        self.password = password
        self.verbose = verbose
        self.my_tftp_address = None
        self.my_tftp_file = None
        
        self.bmc = make_bmc(LanBMC, hostname=ip_address, username=username, 
                            password=password, verbose=verbose)
        #
        # Current TFTP information for this instance
        #
#        self.tftp_server = None
#        self.tftp_address = None
#        self.tftp_file_name = None
#        self.tftp_basename = None
        #atexit.register(self._cleanup)

    
    def get_ipinfo(self, tftp, max_wait_time=10):
        """Get ipv4 information for this node.
        
        :param tftp: TFTP Server to facilitate cmd/response.
        :type tftp: tftp.InternalTftpServer or tftp.ExternalTftpServer
        :param max_wait_time: The maximum amount of seconds to wait for a tftp
                              file to appear.
        :type max_wait_time: integer
        
        :raises NoIpInfoError: When no results are read back in the tftp file
                               for the ipinfo command.
        
        :return: The ipv4 info for this node.
        :rtype: string
        """
        self._tftp_init(tftp)
        #
        # Send ipinfo command ...
        #
        try:
            result = self.bmc.get_fabric_ipinfo(filename=os.path.basename(
                                                         self.my_tftp_file), 
                                                tftp_addr=self.my_tftp_address)

        except IpmiError as error:
            # Re-raise a meaningful IpmiError
            raise IpmiError(self._parse_ipmierror(error))
        
        # @todo: These calls to hasattr() may go away if a command raises 
        # an exception on error?
        if hasattr(result, 'error'):
            raise Exception(result.error)

        #
        # Wait for file for up to 10 seconds ...
        #
        idx = 0
        for idx in range(max_wait_time):
            try:
                time.sleep(1)
                #tftp.get_file(self.tftp_basename, self.tftp_file_name)
                tftp.get_file(tftp.tftp_dir, self.my_tftp_file)
                if os.path.getsize(self.my_tftp_file) > 0:
                    break
            
            # Catch both exceptions, because External raises TftpException, 
            # where Internal give IOError ...
            except (TftpException, IOError) as error:
                if (idx == max_wait_time):
                    # The file never showed up after max_wait_time seconds
                    traceback.format_exc()
                    raise
                if (self.verbose):
                    print ('Attempt %d of %d getting file: %s' % 
                          (idx, max_wait_time, self.my_tftp_file))
        #
        # Ensure file is present
        #
        try:
            with open(self.my_tftp_file) as a_file:
                a_file.close()
        
        except IOError:
            if (self.verbose):
                traceback.format_exc()
            raise
        #
        # Parse addresses from ipinfo file
        #
        results = []
        for line in open(self.my_tftp_file):
            if line.startswith('Node'):
                elements = line.split()
                node = int(elements[1].rstrip(':'))
                address = elements[2]
                if address != '0.0.0.0':
                    results.append((node, address))
        
        results.sort()
        if len(results) == 0:
            raise NoIpInfoError('Failed to retrieve IP info.')
        else:
            return [ip for node, ip in results if (ip == self.ip_address)][0]

    def get_macaddrs(self, tftp, max_wait_time=10):
        """ Download mac addresses from this target 
        
        :param tftp: TFTP Server to facilitate cmd/response.
        :type tftp: tftp.InternalTftpServer or tftp.ExternalTftpServer
        :param max_wait_time: The maximum amount of seconds to wait for a tftp
                              file to appear.
        :type max_wait_time: integer
        
        :raises NoMacAddressError: When no results are read back in the tftp 
                                   file for the ipinfo command.
        
        :return: The ipv4 info for this node.
        :rtype: string
        """
        self._tftp_init(tftp)
        # Send ipinfo command
        try:
            result = self.bmc.get_fabric_macaddresses(filename=os.path.basename
                                                     (self.my_tftp_file), 
                                                     tftp_addr=
                                                     self.my_tftp_address)
        
        except IpmiError as error:
            raise IpmiError(self._parse_ipmierror(error))
        
        if hasattr(result, "error"):
            raise Exception(result.error)

        #
        # Wait for file for up to 10 seconds ...
        #
        idx = 0
        for idx in range(max_wait_time):
            try:
                time.sleep(1)
                #tftp.get_file(self.tftp_basename, self.tftp_file_name)
                tftp.get_file(tftp.tftp_dir, self.my_tftp_file)
                if os.path.getsize(self.my_tftp_file) > 0:
                    break
            
            # Catch both exceptions, because External raises TftpException, 
            # where Internal give IOError ...
            except (TftpException, IOError) as error:
                if (idx == max_wait_time):
                    # The file never showed up after max_wait_time seconds
                    traceback.format_exc()
                    raise
                if (self.verbose):
                    print ('Attempt %d of %d getting file: %s' % 
                          (idx, max_wait_time, self.my_tftp_file))
        #
        # Ensure file is present
        #
        try:
            with open(self.my_tftp_file) as a_file:
                a_file.close()
        
        except IOError:
            if (self.verbose):
                traceback.format_exc()
            raise

        # Parse addresses from macaddrs file
        results = []
        for line in open(self.my_tftp_file):
            if line.startswith("Node"):
                elements = line.split()
                node = int(elements[1].rstrip(","))
                port = int(elements[3].rstrip(":"))
                address = elements[4]
                results.append((node, port, address))
        
        results.sort()
        if len(results) == 0:
            raise NoMacAddressError('Failed to retrieve MacAddress info.')
        else:
            for node, mac_num, mac_addr in results:
                print 'node     = %s' % node 
                print 'mac_num  = %s' % mac_num
                print 'mac_addr = %s' %  mac_addr
                

    def get_power(self):
        """ Return power status reported by IPMI """
        try:
            return self.bmc.get_chassis_status().power_on
        except IpmiError as e:
            raise IpmiError(self._parse_ipmierror(e))

    def set_power(self, mode):
        """ Send an IPMI power command to this target """
        try:
            self.bmc.set_chassis_power(mode=mode)
        except IpmiError as e:
            raise IpmiError(self._parse_ipmierror(e))

    def get_power_policy(self):
        """ Return power status reported by IPMI """
        try:
            return self.bmc.get_chassis_status().power_restore_policy
        except IpmiError as e:
            raise IpmiError(self._parse_ipmierror(e))

    def set_power_policy(self, state):
        """ Set default power state for A9 """
        try:
            self.bmc.set_chassis_policy(state)
        except IpmiError as e:
            raise IpmiError(self._parse_ipmierror(e))

    def mc_reset(self):
        """ Send an IPMI MC reset command to the target """
        try:
            result = self.bmc.mc_reset("cold")
            # @todo: These calls to hasattr() may go away if a command raises 
            # an exception on error?
            if hasattr(result, "error"):
                raise Exception(result.error)
        except IpmiError as e:
            raise IpmiError(self._parse_ipmierror(e))

    def get_sensors(self, name=""):
        """ Get a list of sensors from this target """
        try:
            sensors =  [x for x in self.bmc.sdr_list()
                    if name.lower() in x.sensor_name.lower()]
        except IpmiError as e:
            raise IpmiError(self._parse_ipmierror(e))

        if len(sensors) == 0:
            if name == "":
                raise NoSensorError("No sensors were found")
            else:
                raise NoSensorError("No sensors containing \"%s\" were " +
                                         "found" % name)

        return sensors

    def get_firmware_info(self):
        """ Get firmware info from the target """
        try:
            fwinfo = [x for x in self.bmc.get_firmware_info()
                    if hasattr(x, "partition")]
            if len(fwinfo) == 0:
                raise NoFirmwareInfoError("Failed to retrieve firmware info")

            # Clean up the fwinfo results
            for entry in fwinfo:
                if entry.version == "":
                    entry.version = "Unknown"

            # Flag CDB as "in use" based on socman info
            for a in range(1, len(fwinfo)):
                previous = fwinfo[a-1]
                current = fwinfo[a]
                if (current.type.split()[1][1:-1] == "CDB" and
                        current.in_use == "Unknown"):
                    if previous.type.split()[1][1:-1] != "SOC_ELF":
                        current.in_use = "1"
                    else:
                        current.in_use = previous.in_use
            return fwinfo

        except IpmiError as error_details:
            raise IpmiError(self._parse_ipmierror(error_details))

    def check_firmware(self, package, partition_arg="INACTIVE", priority=None):
        """ Check if this host is ready for an update """
        info = self.info_basic()
        fwinfo = self.get_firmware_info()

        # Check socman version
        if package.required_socman_version:
            soc_version = info.soc_version.lstrip("v")
            required_version = package.required_socman_version.lstrip("v")
            if package.required_socman_version and parse_version(soc_version) \
                    < parse_version(required_version):
                raise SocmanVersionError(
                        "Update requires socman version %s (found %s)"
                        % (required_version, soc_version))

        # Check firmware config
        if info.version != "Unknown" and len(info.version) < 32:
            if package.config == "default" and "slot2" in info.version:
                raise FirmwareConfigError(
                "Refusing to upload a \'default\' package to a \'slot2\' host")
            if package.config == "slot2" and not "slot2" in info.version:
                raise FirmwareConfigError(
                "Refusing to upload a \'slot2\' package to a \'default\' host")

        # Check that the priority can be bumped
        if priority == None:
            image_types = [x.type for x in package.images]
            for partition in fwinfo:
                if (partition.type.split()[1].strip("()") in image_types and
                        int(partition.flags, 16) & 2 == 0):
                    priority = max(priority, int(partition.priority, 16) + 1)
            if priority > 0xFFFF:
                raise PriorityIncrementError(
                      "Unable to increment SIMG priority, too high")

        # Check partitions
        for image in package.images:
            if image.type == "UBOOTENV" or partition_arg == "BOTH":
                self._get_partition(fwinfo, image.type, "FIRST")
                self._get_partition(fwinfo, image.type, "SECOND")
            else:
                self._get_partition(fwinfo, image.type, partition_arg)

    def update_firmware(self, tftp, package, partition_arg="INACTIVE",
            priority=None):
        """ Update firmware on this target. """
        fwinfo = self.get_firmware_info()

        # Get the new priority
        if priority == None:
            image_types = [x.type for x in package.images]
            for partition in fwinfo:
                # Make sure this partition is one of the types we're updating
                # and that the partition is flagged as "active"
                if (partition.type.split()[1].strip("()") in image_types and
                        int(partition.flags, 16) & 2 == 0):
                    priority = max(priority, int(partition.priority, 16) + 1)
            if priority > 0xFFFF:
                raise PriorityIncrementError(
                                "Unable to increment SIMG priority, too high")

        for image in package.images:
            if image.type == "UBOOTENV":
                # Get partitions
                running_part = self._get_partition(fwinfo, image.type, "FIRST")
                factory_part = self._get_partition(fwinfo, image.type,
                        "SECOND")

                # Update factory ubootenv
                self._upload_image(tftp, image, factory_part, priority)

                # Update running ubootenv
                old_ubootenv_image = self._download_image(tftp, running_part)
                old_ubootenv = UbootEnv(open(
                                        old_ubootenv_image.filename).read())
                if "bootcmd_default" in old_ubootenv.variables:
                    ubootenv = UbootEnv(open(image.filename).read())
                    ubootenv.variables["bootcmd_default"] = \
                            old_ubootenv.variables["bootcmd_default"]

                    fd, filename = tempfile.mkstemp(dir=TFTP_DIR)
                    with os.fdopen(fd, "w") as f:
                        f.write(ubootenv.get_contents())
                    ubootenv_image = Image(filename, image.type, False, 
                                           image.daddr, image.skip_crc32,
                                           image.version)
                    self._upload_image(tftp, ubootenv_image, running_part,
                            priority)
                else:
                    self._upload_image(tftp, image, running_part, priority)

            else:
                # Get the partitions
                if partition_arg == "BOTH":
                    partitions = [self._get_partition(fwinfo, image.type,
                            "FIRST"), self._get_partition(fwinfo, image.type,
                            "SECOND")]
                else:
                    partitions = [self._get_partition(fwinfo, image.type,
                            partition_arg)]

                # Update the image
                for partition in partitions:
                    self._upload_image(tftp, image, partition, priority)

        if package.version:
            self.bmc.set_firmware_version(package.version)

    def config_reset(self, tftp):
        """ Reset configuration to factory default """
        try:
            # Reset CDB
            result = self.bmc.reset_firmware()
            if hasattr(result, "error"):
                raise Exception(result.error)

            # Reset ubootenv
            fwinfo = self.get_firmware_info()
            running_part = self._get_partition(fwinfo, "UBOOTENV", "FIRST")
            factory_part = self._get_partition(fwinfo, "UBOOTENV", "SECOND")
            image = self._download_image(tftp, factory_part)
            self._upload_image(tftp, image, running_part)

            # Clear SEL
            self.bmc.sel_clear()

        except IpmiError as e:
            raise IpmiError(self._parse_ipmierror(e))

    def set_boot_order(self, tftp, boot_args):
        """ Set boot order """
        fwinfo = self.get_firmware_info()
        first_part = self._get_partition(fwinfo, "UBOOTENV", "FIRST")
        active_part = self._get_partition(fwinfo, "UBOOTENV", "ACTIVE")

        # Download active ubootenv, modify, then upload to first partition
        image = self._download_image(tftp, active_part)
        ubootenv = UbootEnv(open(image.filename).read())
        ubootenv.set_boot_order(boot_args)
        priority = max(int(x.priority, 16) for x in [first_part, active_part])

        fd, filename = tempfile.mkstemp(dir=TFTP_DIR)
        with os.fdopen(fd, "w") as f:
            f.write(ubootenv.get_contents())
        ubootenv_image = Image(filename, image.type, False,
                image.daddr, image.skip_crc32, image.version)
        self._upload_image(tftp, ubootenv_image, first_part, priority)

    def get_boot_order(self, tftp):
        """ Get boot order """
        return self.get_ubootenv(tftp).get_boot_order()

    def info_basic(self):
        """ Get basic SoC info from this target """
        result = self.bmc.get_info_basic()
        # @todo: These calls to hasattr() may go away if a command raises 
        # an exception on error?
        if hasattr(result, "error"):
            raise Exception(result.error)

        result.soc_version = "v%s" % result.soc_version

        fwinfo = self.get_firmware_info()
        components = [
            ("cdb_version", "CDB"),
            ("stage2_version", "S2_ELF"),
            ("bootlog_version", "BOOT_LOG"),
            ("a9boot_version", "A9_EXEC"),
            ("uboot_version", "A9_UBOOT"),
            ("ubootenv_version", "UBOOTENV"),
            ("dtb_version", "DTB")
        ]
        for var, ptype in components:
            try:
                partition = self._get_partition(fwinfo, ptype, "ACTIVE")
                setattr(result, var, partition.version)
            
            except NoPartitionError:
                pass

        try:
            card = self.bmc.get_info_card()
            setattr(result, "card", "%s X%02i" %
                    (card.type, int(card.revision)))
        except IpmiError:
            # Should raise a cxmanage error, but we want to allow the command
            # to continue gracefully if socman is out of date.
            setattr(result, "card", "Unknown")

        return result

    def info_dump(self, tftp):
        """ Dump info from this target """
        return get_info_dump(tftp, self)

    def ipmitool_command(self, ipmitool_args):
        """ Execute an arbitrary ipmitool command """
        if "IPMITOOL_PATH" in os.environ:
            command = [os.environ["IPMITOOL_PATH"]]
        else:
            command = ["ipmitool"]

        command += ["-U", self.username, "-P", self.password, "-H",
                self.ip_address]
        command += ipmitool_args

        if (self.verbose):
            print "Running %s" % " ".join(command)

        process = subprocess.Popen(command, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        return (stdout + stderr).strip()

    def get_ubootenv(self, tftp):
        """ Get the active u-boot environment """
        fwinfo = self.get_firmware_info()
        partition = self._get_partition(fwinfo, "UBOOTENV", "ACTIVE")
        image = self._download_image(tftp, partition)
        return UbootEnv(open(image.filename).read())

    def _get_partition(self, fwinfo, image_type, partition_arg):
        """ Get a partition for this image type based on the argument """
        # Filter partitions for this type
        partitions = [x for x in fwinfo if
                x.type.split()[1][1:-1] == image_type]
        if len(partitions) < 1:
            raise NoPartitionError("No partition of type %s found on host"
                    % image_type)

        if partition_arg == "FIRST":
            return partitions[0]
        elif partition_arg == "SECOND":
            if len(partitions) < 2:
                raise NoPartitionError("No second partition found on host")
            return partitions[1]
        elif partition_arg == "OLDEST":
            # Return the oldest partition
            partitions.sort(key=lambda x: x.partition, reverse=True)
            partitions.sort(key=lambda x: x.priority)
            return partitions[0]
        elif partition_arg == "NEWEST":
            # Return the newest partition
            partitions.sort(key=lambda x: x.partition)
            partitions.sort(key=lambda x: x.priority, reverse=True)
            return partitions[0]
        elif partition_arg == "INACTIVE":
            # Return the partition that's not in use (or least likely to be)
            partitions.sort(key=lambda x: x.partition, reverse=True)
            partitions.sort(key=lambda x: x.priority)
            partitions.sort(key=lambda x: int(x.flags, 16) & 2 == 0)
            partitions.sort(key=lambda x: x.in_use == "1")
            return partitions[0]
        elif partition_arg == "ACTIVE":
            # Return the partition that's in use (or most likely to be)
            partitions.sort(key=lambda x: x.partition)
            partitions.sort(key=lambda x: x.priority, reverse=True)
            partitions.sort(key=lambda x: int(x.flags, 16) & 2 == 1)
            partitions.sort(key=lambda x: x.in_use == "0")
            return partitions[0]
        else:
            raise ValueError("Invalid partition argument: %s" % partition_arg)

    def _upload_image(self, tftp, image, partition, priority=None):
        """ Upload a single image. This includes uploading the image,
        performing the firmware update, crc32 check, and activation."""
        #tftp_address = "%s:%s" % (tftp.get_address(self.ip_address),
        #        tftp.get_port())
        self._tftp_init(tftp)
        partition_id = int(partition.partition)
        if priority == None:
            priority = int(partition.priority, 16)
        daddr = int(partition.daddr, 16)

        # Check image size
        if image.size() > int(partition.size, 16):
            raise ImageSizeError("%s image is too large for partition %i" %
                    image.type, partition_id)

        # Upload image to tftp server
        filename = image.upload(tftp, priority, daddr)

        while True:
            try:
                # Update the firmware
                result = self.bmc.update_firmware(filename,
                                        partition_id, image.type, tftp_address)
                if not hasattr(result, "tftp_handle_id"):
                    raise AttributeError("Failed to start firmware upload")
                self._wait_for_transfer(result.tftp_handle_id)

                # Verify crc and activate
                result = self.bmc.check_firmware(partition_id)
                if not hasattr(result, "crc32") or result.error != None:
                    # @todo: Is this the right Exception to raise?
                    raise AttributeError("Node reported crc32 check failure")
                self.bmc.activate_firmware(partition_id)

                break
            
            except Exception:
                if (self.verbose):
                    traceback.format_exc()
                raise

    def _download_image(self, tftp, partition):
        """ Download an image from the target.

        Returns an image. """
        tftp_address = "%s:%s" % (tftp.get_address(self.ip_address),
                tftp.get_port())

        # Download the image
        fd, filename = tempfile.mkstemp(dir=tftp.tftp_dir)
        os.close(fd)
        basename = os.path.basename(filename)
        partition_id = int(partition.partition)
        image_type = partition.type.split()[1][1:-1]

        while True:
            try:
                result = self.bmc.retrieve_firmware(basename, partition_id,
                        image_type, tftp_address)
                if not hasattr(result, "tftp_handle_id"):
                    raise AttributeError("Failed to start firmware download")
                self._wait_for_transfer(result.tftp_handle_id)
                break
            
            except Exception:
                if (self.verbose):
                    traceback.format_exc()
                raise

        tftp.get_file(basename, filename)

        return Image(filename, image_type, daddr=int(partition.daddr, 16), 
                     version=partition.version)

    def _wait_for_transfer(self, handle):
        """Wait for a firmware transfer to finish.
        
        :param handle: Handle to send commands over.
        :type handle: 
        """
        deadline = time.time() + 180

        result = self.bmc.get_firmware_status(handle)
        if not hasattr(result, "status"):
            raise AttributeError('Failed to retrieve firmware transfer status')

        while result.status == "In progress":
            if time.time() >= deadline:
                raise TimeoutError("Transfer timed out after 3 minutes")

            time.sleep(1)

            result = self.bmc.get_firmware_status(handle)
            if not hasattr(result, "status"):
                raise AttributeError("Failed to retrieve transfer info")

        if result.status != "Complete":
            raise TransferFailure("Node reported transfer failure")

    def _parse_ipmierror(self, error_details):
        """ Parse a meaningful message from an IpmiError """
        try:
            error = str(error_details).lstrip().splitlines()[0].rstrip()
            if error.startswith('Error: '):
                error = error[7:]
            return 'IPMItool ERROR: %s' % error
        
        except IndexError:
            return 'IPMITool encountered an error.'

    def _tftp_init(self, tftp):
        """Sets the current tftp server/client information for this class.
        Creates the temporary FILE for communication.
        
        :param tftp: TFTP server(or client) to connect to.
        :type tftp: tftp.InternalTftp or tftp.ExternalTftp
        """
        self.my_tftp_address = '%s:%s' % (tftp.get_address(
                                          relative_host=self.ip_address), 
                                          tftp.get_port())
        f_hndl, self.my_tftp_file = tempfile.mkstemp(dir=tftp.tftp_dir)
        #self.my_tftp_file = os.path.basename(self.my_tftp_file)
        os.close(f_hndl)
#        self.tftp_address = '%s:%s' % (tftp.get_address(
#                                       relative_host=self.ip_address), 
#                                       tftp.get_port())

        #self.tftp_basename = os.path.basename(self.tftp_file_name)
    
    def _cleanup(self):
        """Removes the TFTP temporary FILE."""
        if (self.tftp_server):
            shutil.rmtree(self.tftp_server.tftp_dir)
        
# End of file: node.py

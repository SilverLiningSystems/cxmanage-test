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


""" Target objects used by the cxmanage controller """

import atexit
import os
import shutil
import subprocess
import tempfile
import time

from cxmanage import CxmanageError
from cxmanage.image import Image
from cxmanage.ubootenv import UbootEnv
from cxmanage.infodump import get_info_dump

from pyipmi import make_bmc, IpmiError
from pyipmi.bmc import LanBMC

class Target:
    """ Contains info for a single target. A target consists of a hostname,
    an username, and a password. """

    def __init__(self, address, username="admin", password="admin",
            verbosity=0, bmc_class=LanBMC, ubootenv_class=UbootEnv):
        self.address = address
        self.username = username
        self.password = password
        self.verbosity = verbosity
        self.ubootenv_class = ubootenv_class

        self.work_dir = tempfile.mkdtemp(prefix="cxmanage-target-")
        atexit.register(self._cleanup)

        verbose = verbosity >= 2
        self.bmc = make_bmc(bmc_class, hostname=address,
                username=username, password=password, verbose=verbose)

    def _cleanup(self):
        """ Clean up temporary files """
        if os.path.exists(self.work_dir):
            shutil.rmtree(self.work_dir)

    def get_ipinfo(self, tftp):
        """ Download IP info from this target """
        tftp_address = "%s:%s" % (tftp.get_address(self.address),
                tftp.get_port())

        filename = tempfile.mkstemp(prefix="%s/ip_" % self.work_dir)[1]
        basename = os.path.basename(filename)

        # Send ipinfo command
        try:
            result = self.bmc.get_fabric_ipinfo(basename, tftp_address)
        except IpmiError as e:
            raise CxmanageError(self._parse_ipmierror(e))
        if hasattr(result, "error"):
            raise CxmanageError(result.error)

        # Wait for file
        for a in range(10):
            try:
                time.sleep(1)
                tftp.get_file(basename, filename)
                if os.path.getsize(filename) > 0:
                    break
            except CxmanageError:
                pass

        # Ensure file is present
        if not os.path.exists(filename):
            raise CxmanageError("Failed to retrieve IP info")

        # Parse addresses from ipinfo file
        results = []
        for line in open(filename):
            if line.startswith("Node"):
                elements = line.split()
                node = int(elements[1].rstrip(":"))
                address = elements[2]
                if address != "0.0.0.0":
                    results.append((node, address))
        results.sort()

        # Make sure we found something
        if len(results) == 0:
            raise CxmanageError("Failed to retrieve IP info")

        return results

    def get_macaddrs(self, tftp):
        """ Download mac addresses from this target """
        tftp_address = "%s:%s" % (tftp.get_address(self.address),
                tftp.get_port())

        filename = tempfile.mkstemp(prefix="%s/mac_" % self.work_dir)[1]
        basename = os.path.basename(filename)

        # Send ipinfo command
        try:
            result = self.bmc.get_fabric_macaddresses(basename, tftp_address)
        except IpmiError as e:
            raise CxmanageError(self._parse_ipmierror(e))
        if hasattr(result, "error"):
            raise CxmanageError(result.error)

        # Wait for file
        for a in range(10):
            try:
                time.sleep(1)
                tftp.get_file(basename, filename)
                if os.path.getsize(filename) > 0:
                    break
            except CxmanageError:
                pass

        # Ensure file is present
        if not os.path.exists(filename):
            raise CxmanageError("Failed to retrieve mac addresses")

        # Parse addresses from macaddrs file
        results = []
        for line in open(filename):
            if line.startswith("Node"):
                elements = line.split()
                node = int(elements[1].rstrip(","))
                port = int(elements[3].rstrip(":"))
                address = elements[4]
                results.append((node, port, address))
        results.sort()

        # Make sure we found something
        if len(results) == 0:
            raise CxmanageError("Failed to retrieve mac addresses")

        return results

    def get_power(self):
        """ Return power status reported by IPMI """
        try:
            return self.bmc.get_chassis_status().power_on
        except IpmiError as e:
            raise CxmanageError(self._parse_ipmierror(e))

    def set_power(self, mode):
        """ Send an IPMI power command to this target """
        try:
            self.bmc.set_chassis_power(mode=mode)
        except IpmiError as e:
            raise CxmanageError(self._parse_ipmierror(e))

    def get_power_policy(self):
        """ Return power status reported by IPMI """
        try:
            return self.bmc.get_chassis_status().power_restore_policy
        except IpmiError as e:
            raise CxmanageError(self._parse_ipmierror(e))

    def set_power_policy(self, state):
        """ Set default power state for A9 """
        try:
            self.bmc.set_chassis_policy(state)
        except IpmiError as e:
            raise CxmanageError(self._parse_ipmierror(e))

    def mc_reset(self):
        """ Send an IPMI MC reset command to the target """
        try:
            result = self.bmc.mc_reset("cold")
            if hasattr(result, "error"):
                raise CxmanageError(result.error)
        except IpmiError as e:
            raise CxmanageError(self._parse_ipmierror(e))

    def get_sensors(self, name=""):
        """ Get a list of sensors from this target """
        try:
            sensors =  [x for x in self.bmc.sdr_list()
                    if name.lower() in x.sensor_name.lower()]
        except IpmiError as e:
            raise CxmanageError(self._parse_ipmierror(e))

        if len(sensors) == 0:
            if name == "":
                raise CxmanageError("No sensors were found")
            else:
                raise CxmanageError("No sensors containing \"%s\" were found"
                        % name)

        return sensors

    def get_firmware_info(self):
        """ Get firmware info from the target """
        try:
            fwinfo = [x for x in self.bmc.get_firmware_info()
                    if hasattr(x, "partition")]
            if len(fwinfo) == 0:
                raise CxmanageError("Failed to retrieve firmware info")

            # For compatibility with old ipmitool versions, make sure
            # we have a "priority" field. It used to be called "version"
            for entry in fwinfo:
                if not hasattr(entry, "priority"):
                    entry.priority = entry.version
                    entry.version = "Unknown"

            # TODO: remove this later
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

        except IpmiError as e:
            raise CxmanageError(self._parse_ipmierror(e))

    def update_firmware(self, tftp, images, partition_arg="INACTIVE"):
        """ Update firmware on this target. """
        fwinfo = self.get_firmware_info()

        # Get the new priority
        priority = 0
        image_types = [x.type for x in images]
        for partition in fwinfo:
            # Make sure this partition is one of the types we're updating
            # and that the partition is flagged as "active"
            if (partition.type.split()[1][1:-1] in image_types and
                    int(partition.flags, 16) & 2 == 0):
                priority = max(priority, int(partition.priority, 16) + 1)
        if priority > 0xFFFF:
            raise CxmanageError("Unable to increment SIMG priority, too high")

        for image in images:
            if image.type == "UBOOTENV":
                # Get partitions
                running_part = self._get_partition(fwinfo, image.type, "FIRST")
                factory_part = self._get_partition(fwinfo, image.type,
                        "SECOND")

                # Update running ubootenv
                old_ubootenv = self._download_ubootenv(tftp, running_part)
                if "bootcmd_default" in old_ubootenv.variables:
                    bootcmd = old_ubootenv.variables["bootcmd_default"]
                    contents = open(image.filename).read()
                    if image.simg:
                        contents = contents[28:]
                    ubootenv = self.ubootenv_class(contents)
                    ubootenv.variables["bootcmd_default"] = bootcmd
                    self._upload_ubootenv(tftp, ubootenv,
                            running_part, priority)
                else:
                    self._upload_image(tftp, image, running_part, priority)

                # Update factory ubootenv
                self._upload_image(tftp, image, factory_part, priority)

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

    def config_reset(self, tftp):
        """ Reset configuration to factory default """
        try:
            # Reset CDB
            result = self.bmc.reset_firmware()
            if hasattr(result, "error"):
                raise CxmanageError(result.error)

            # Reset ubootenv
            fwinfo = self.get_firmware_info()
            running_part = self._get_partition(fwinfo, "UBOOTENV", "FIRST")
            factory_part = self._get_partition(fwinfo, "UBOOTENV", "SECOND")
            image = self._download_image(tftp, factory_part)
            self._upload_image(tftp, image, running_part)

            # Clear SEL
            self.bmc.sel_clear()

        except IpmiError as e:
            raise CxmanageError(self._parse_ipmierror(e))

    def set_boot_order(self, tftp, boot_args):
        """ Set boot order """
        fwinfo = self.get_firmware_info()
        first_part = self._get_partition(fwinfo, "UBOOTENV", "FIRST")
        active_part = self._get_partition(fwinfo, "UBOOTENV", "ACTIVE")

        # Download active ubootenv, modify, then upload to first partition
        ubootenv = self._download_ubootenv(tftp, active_part)
        ubootenv.set_boot_order(boot_args)
        priority = max(int(x.priority, 16) for x in [first_part, active_part])
        self._upload_ubootenv(tftp, ubootenv, first_part, priority)

    def get_boot_order(self, tftp):
        """ Get boot order """
        fwinfo = self.get_firmware_info()
        active_part = self._get_partition(fwinfo, "UBOOTENV", "ACTIVE")
        ubootenv = self._download_ubootenv(tftp, active_part)
        return ubootenv.get_boot_order()

    def info_basic(self):
        """ Get basic SoC info from this target """
        result = self.bmc.get_info_basic()
        if hasattr(result, "error"):
            raise CxmanageError(result.error)

        fwinfo = self.get_firmware_info()

        try:
            a9boot_partition = self._get_partition(fwinfo, "A9_EXEC", "ACTIVE")
            setattr(result, "a9boot_version", a9boot_partition.version)
        except CxmanageError:
            pass

        try:
            uboot_partition = self._get_partition(fwinfo, "A9_UBOOT", "ACTIVE")
            setattr(result, "uboot_version", uboot_partition.version)
        except CxmanageError:
            pass

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
                self.address]
        command += ipmitool_args

        if self.verbosity >= 2:
            print "Running %s" % " ".join(command)

        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        return (stdout + stderr).strip()

    def get_ubootenv(self, tftp):
        """ Get the active u-boot environment """
        fwinfo = self.get_firmware_info()
        partition = self._get_partition(fwinfo, "UBOOTENV", "ACTIVE")

        return self._download_ubootenv(tftp, partition)

    def _get_partition(self, fwinfo, image_type, partition_arg):
        """ Get a partition for this image type based on the argument """
        # Filter partitions for this type
        partitions = [x for x in fwinfo if
                x.type.split()[1][1:-1] == image_type]
        if len(partitions) < 1:
            raise CxmanageError("No partitions found on host")

        if partition_arg == "FIRST":
            return partitions[0]
        elif partition_arg == "SECOND":
            if len(partitions) < 2:
                raise CxmanageError("No second partition found on host")
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
        tftp_address = "%s:%s" % (tftp.get_address(self.address),
                tftp.get_port())

        partition_id = int(partition.partition)
        if priority == None:
            priority = int(partition.priority, 16)
        daddr = int(partition.daddr, 16)

        # Check image size
        if image.size() > int(partition.size, 16):
            raise CxmanageError("%s image is too large for partition %i" %
                    image.type, partition_id)

        # Upload image to tftp server
        filename = image.upload(self.work_dir, tftp, priority, daddr)

        errors = 0
        while True:
            try:
                # Update the firmware
                result = self.bmc.update_firmware(filename,
                        partition_id, image.type, tftp_address)
                if hasattr(result, "fw_error") and result.fw_error != None:
                    raise CxmanageError(result.fw_error)
                self._wait_for_transfer(result.tftp_handle_id)

                # Verify crc and activate
                result = self.bmc.check_firmware(partition_id)
                if hasattr(result, "crc32") and result.error == None:
                    self.bmc.activate_firmware(partition_id)
                else:
                    raise CxmanageError("Node reported crc32 check failure")

                break

            except CxmanageError as e:
                errors += 1
                if errors >= 3:
                    raise e

    def _download_image(self, tftp, partition):
        """ Download an image from the target.

        Returns the filename. """
        tftp_address = "%s:%s" % (tftp.get_address(self.address),
                tftp.get_port())

        # Download the image
        filename = tempfile.mkstemp(prefix="%s/img_" % self.work_dir)[1]
        basename = os.path.basename(filename)
        partition_id = int(partition.partition)
        image_type = partition.type.split()[1][1:-1]

        errors = 0
        while True:
            try:
                result = self.bmc.retrieve_firmware(basename, partition_id,
                        image_type, tftp_address)
                if hasattr(result, "fw_error") and result.fw_error != None:
                    raise CxmanageError(result.fw_error)
                self._wait_for_transfer(result.tftp_handle_id)
                break
            except CxmanageError as e:
                errors += 1
                if errors >= 3:
                    raise e

        tftp.get_file(basename, filename)

        return Image(filename, image_type)

    def _upload_ubootenv(self, tftp, ubootenv, partition, priority=None):
        """ Upload a uboot environment to the target """
        filename = tempfile.mkstemp(prefix="%s/env_" % self.work_dir)[1]
        open(filename, "w").write(ubootenv.get_contents())
        image = Image(filename, "UBOOTENV")
        self._upload_image(tftp, image, partition, priority)

    def _download_ubootenv(self, tftp, partition):
        """ Download a uboot environment from the target """
        image = self._download_image(tftp, partition)

        # Open the file
        simg = open(image.filename).read()
        return self.ubootenv_class(simg[28:])

    def _wait_for_transfer(self, handle):
        """ Wait for a firmware transfer to finish"""
        deadline = time.time() + 180

        result = self.bmc.get_firmware_status(handle)
        if not hasattr(result, "status"):
            raise CxmanageError("Unable to retrieve transfer info")

        while result.status == "In progress":
            if time.time() >= deadline:
                raise CxmanageError("Transfer timed out after 3 minutes")

            time.sleep(1)

            result = self.bmc.get_firmware_status(handle)
            if not hasattr(result, "status"):
                raise CxmanageError("Unable to retrieve transfer info")

        if result.status != "Complete":
            raise CxmanageError("Node reported transfer failure")

    def _parse_ipmierror(self, e):
        """ Parse a meaningful message from an IpmiError """
        error = str(e).lstrip().splitlines()[0].rstrip()
        if error.startswith("Error: "):
            error = error[7:]
        return "IPMItool error (%s)" % error

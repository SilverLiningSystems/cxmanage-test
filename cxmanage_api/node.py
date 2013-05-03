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


import os
import re
import subprocess
import time

from pkg_resources import parse_version
from pyipmi import make_bmc, IpmiError
from pyipmi.bmc import LanBMC as BMC
from tftpy.TftpShared import TftpException

from cxmanage_api import temp_file
from cxmanage_api.tftp import InternalTftp, ExternalTftp
from cxmanage_api.image import Image as IMAGE
from cxmanage_api.ubootenv import UbootEnv as UBOOTENV
from cxmanage_api.ip_retriever import IPRetriever as IPRETRIEVER
from cxmanage_api.cx_exceptions import TimeoutError, NoSensorError, \
        NoFirmwareInfoError, SocmanVersionError, FirmwareConfigError, \
        PriorityIncrementError, NoPartitionError, TransferFailure, \
        ImageSizeError, PartitionInUseError


class Node(object):
    """A node is a single instance of an ECME.

    >>> # Typical usage ...
    >>> from cxmanage_api.node import Node
    >>> node = Node(ip_adress='10.20.1.9', verbose=True)

    :param ip_address: The ip_address of the Node.
    :type ip_address: string
    :param username: The login username credential. [Default admin]
    :type username: string
    :param password: The login password credential. [Default admin]
    :type password: string
    :param tftp: The internal/external TFTP server to use for data xfer.
    :type tftp: `Tftp <tftp.html>`_
    :param verbose: Flag to turn on verbose output (cmd/response).
    :type verbose: boolean
    :param bmc: BMC object for this Node. Default: pyipmi.bmc.LanBMC
    :type bmc: BMC
    :param image: Image object for this node. Default cxmanage_api.Image
    :type image: `Image <image.html>`_
    :param ubootenv: UbootEnv  for this node. Default cxmanage_api.UbootEnv
    :type ubootenv: `UbootEnv <ubootenv.html>`_

    """

    def __init__(self, ip_address, username="admin", password="admin",
                  tftp=None, ecme_tftp_port=5001, verbose=False, bmc=None,
                  image=None, ubootenv=None, ipretriever=None):
        """Default constructor for the Node class."""
        if (not tftp):
            tftp = InternalTftp()

        # Dependency Integration
        if (not bmc):
            bmc = BMC
        if (not image):
            image = IMAGE
        if (not ubootenv):
            ubootenv = UBOOTENV
        if (not ipretriever):
            ipretriever = IPRETRIEVER

        self.ip_address = ip_address
        self.username = username
        self.password = password
        self.tftp = tftp
        self.ecme_tftp = ExternalTftp(ip_address, ecme_tftp_port)
        self.verbose = verbose

        self.bmc = make_bmc(bmc, hostname=ip_address, username=username,
                            password=password, verbose=verbose)
        self.image = image
        self.ubootenv = ubootenv
        self.ipretriever = ipretriever

        self._node_id = None

    def __eq__(self, other):
        return isinstance(other, Node) and self.ip_address == other.ip_address

    def __hash__(self):
        return hash(self.ip_address)

    def __str__(self):
        return 'Node: %s' % self.ip_address

    @property
    def tftp_address(self):
        """Returns the tftp_address (ip:port) that this node is using.

        >>> node.tftp_address
        '10.20.2.172:35123'

        :returns: The tftp address and port that this node is using.
        :rtype: string

        """
        return '%s:%s' % (self.tftp.get_address(relative_host=self.ip_address),
                          self.tftp.port)

    @property
    def node_id(self):
        """ Returns the numerical ID for this node.

        >>> node.node_id
        0

        :returns: The ID of this node.
        :rtype: integer

        """
        if self._node_id == None:
            self._node_id = self.bmc.fabric_get_node_id()
        return self._node_id

    @node_id.setter
    def node_id(self, value):
        """ Sets the ID for this node.

        :param value: The value we want to set.
        :type value: integer

        """
        self._node_id = value

    def get_mac_addresses(self):
        """Gets a dictionary of MAC addresses for this node. The dictionary
        maps each port/interface to a list of MAC addresses for that interface.

        >>> node.get_mac_addresses()
        {
         0: ['fc:2f:40:3b:ec:40'],
         1: ['fc:2f:40:3b:ec:41'],
         2: ['fc:2f:40:3b:ec:42']
        }

        :return: MAC Addresses for all interfaces.
        :rtype: dictionary

        """
        return self.get_fabric_macaddrs()[self.node_id]

    def add_macaddr(self, iface, macaddr):
        """Add mac address on an interface

        >>> node.add_macaddr(iface, macaddr)

        :param iface: Interface to add to
        :type iface: integer
        :param macaddr: MAC address to add
        :type macaddr: string

        :raises IpmiError: If errors in the command occur with BMC communication.

        """
        self.bmc.fabric_add_macaddr(iface=iface, macaddr=macaddr)

    def rm_macaddr(self, iface, macaddr):
        """Remove mac address from an interface

        >>> node.rm_macaddr(iface, macaddr)

        :param iface: Interface to remove from
        :type iface: integer
        :param macaddr: MAC address to remove
        :type macaddr: string

        :raises IpmiError: If errors in the command occur with BMC communication.

        """
        self.bmc.fabric_rm_macaddr(iface=iface, macaddr=macaddr)

    def get_power(self):
        """Returns the power status for this node.

        >>> # Powered ON system ...
        >>> node.get_power()
        True
        >>> # Powered OFF system ...
        >>> node.get_power()
        False

        :return: The power state of the Node.
        :rtype: boolean

        """
        try:
            return self.bmc.get_chassis_status().power_on
        except IpmiError as e:
            raise IpmiError(self._parse_ipmierror(e))

    def set_power(self, mode):
        """Send an IPMI power command to this target.

        >>> # To turn the power 'off'
        >>> node.set_power(mode='off')
        >>> # A quick 'get' to see if it took effect ...
        >>> node.get_power()
        False

        >>> # To turn the power 'on'
        >>> node.set_power(mode='on')

        :param mode: Mode to set the power state to. ('on'/'off')
        :type mode: string

        """
        try:
            self.bmc.set_chassis_power(mode=mode)
        except IpmiError as e:
            raise IpmiError(self._parse_ipmierror(e))

    def get_power_policy(self):
        """Return power status reported by IPMI.

        >>> node.get_power_policy()
        'always-off'

        :return: The Nodes current power policy.
        :rtype: string

        :raises IpmiError: If errors in the command occur with BMC communication.

        """
        try:
            return self.bmc.get_chassis_status().power_restore_policy
        except IpmiError as e:
            raise IpmiError(self._parse_ipmierror(e))

    def set_power_policy(self, state):
        """Set default power state for Linux side.

        >>> # Set the state to 'always-on'
        >>> node.set_power_policy(state='always-on')
        >>> # A quick check to make sure our setting took ...
        >>> node.get_power_policy()
        'always-on'

        :param state: State to set the power policy to.
        :type state: string

        """
        try:
            self.bmc.set_chassis_policy(state)
        except IpmiError as e:
            raise IpmiError(self._parse_ipmierror(e))

    def mc_reset(self, wait=False):
        """Sends a Master Control reset command to the node.

        >>> node.mc_reset()

        :param wait: Wait for the node to come back up.
        :type wait: boolean

        :raises Exception: If the BMC command contains errors.
        :raises IPMIError: If there is an IPMI error communicating with the BMC.

        """
        try:
            result = self.bmc.mc_reset("cold")
            if (hasattr(result, "error")):
                raise Exception(result.error)
        except IpmiError as e:
            raise IpmiError(self._parse_ipmierror(e))

        if wait:
            deadline = time.time() + 300.0

            # Wait for it to go down...
            time.sleep(60)

            # Now wait to come back up!
            while time.time() < deadline:
                time.sleep(1)
                try:
                    self.bmc.get_info_basic()
                    break
                except IpmiError:
                    pass
            else:
                raise Exception("Reset timed out")

    def get_sensors(self, search=""):
        """Get a list of sensor objects that match search criteria.

        .. note::
            * If no sensor name is specified, ALL sensors will be returned.

        >>> # Get ALL sensors ...
        >>> node.get_sensors()
        {
         'MP Temp 0'        : <pyipmi.sdr.AnalogSdr object at 0x1e63890>,
         'Temp 0'           : <pyipmi.sdr.AnalogSdr object at 0x1e63410>,
         'Temp 1'           : <pyipmi.sdr.AnalogSdr object at 0x1e638d0>,
         'Temp 2'           : <pyipmi.sdr.AnalogSdr object at 0x1e63690>,
         'Temp 3'           : <pyipmi.sdr.AnalogSdr object at 0x1e63950>,
         'VCORE Voltage'    : <pyipmi.sdr.AnalogSdr object at 0x1e63bd0>,
         'TOP Temp 2'       : <pyipmi.sdr.AnalogSdr object at 0x1e63ad0>,
         'TOP Temp 1'       : <pyipmi.sdr.AnalogSdr object at 0x1e63a50>,
         'TOP Temp 0'       : <pyipmi.sdr.AnalogSdr object at 0x1e639d0>,
         'VCORE Current'    : <pyipmi.sdr.AnalogSdr object at 0x1e63710>,
         'V18 Voltage'      : <pyipmi.sdr.AnalogSdr object at 0x1e63b50>,
         'V09 Current'      : <pyipmi.sdr.AnalogSdr object at 0x1e63990>,
         'Node Power'       : <pyipmi.sdr.AnalogSdr object at 0x1e63cd0>,
         'DRAM VDD Current' : <pyipmi.sdr.AnalogSdr object at 0x1e63910>,
         'DRAM VDD Voltage' : <pyipmi.sdr.AnalogSdr object at 0x1e634d0>,
         'V18 Current'      : <pyipmi.sdr.AnalogSdr object at 0x1e63c50>,
         'VCORE Power'      : <pyipmi.sdr.AnalogSdr object at 0x1e63c90>,
         'V09 Voltage'      : <pyipmi.sdr.AnalogSdr object at 0x1e63b90>
        }
        >>> # Get ANY sensor that 'contains' the substring of search in it ...
        >>> node.get_sensors(search='Temp 0')
        {
         'MP Temp 0'  : <pyipmi.sdr.AnalogSdr object at 0x1e63810>,
         'TOP Temp 0' : <pyipmi.sdr.AnalogSdr object at 0x1e63850>,
         'Temp 0'     : <pyipmi.sdr.AnalogSdr object at 0x1e63510>
        }

        :param search: Name of the sensor you wish to search for.
        :type search: string

        :return: Sensor information.
        :rtype: dictionary of pyipmi objects

        """
        try:
            sensors = [x for x in self.bmc.sdr_list()
                        if search.lower() in x.sensor_name.lower()]
        except IpmiError as e:
            raise IpmiError(self._parse_ipmierror(e))

        if (len(sensors) == 0):
            if (search == ""):
                raise NoSensorError("No sensors were found")
            else:
                raise NoSensorError("No sensors containing \"%s\" were " +
                                    "found" % search)
        return dict((x.sensor_name, x) for x in sensors)

    def get_sensors_dict(self, search=""):
        """Get a list of sensor dictionaries that match search criteria.

        >>> node.get_sensors_dict()
        {
         'DRAM VDD Current':
            {
             'entity_id'              : '7.1',
             'event_message_control'  : 'Per-threshold',
             'lower_critical'         : '34.200',
             'lower_non_critical'     : '34.200',
             'lower_non_recoverable'  : '34.200',
             'maximum_sensor_range'   : 'Unspecified',
             'minimum_sensor_range'   : 'Unspecified',
             'negative_hysteresis'    : '0.800',
             'nominal_reading'        : '50.200',
             'normal_maximum'         : '34.200',
             'normal_minimum'         : '34.200',
             'positive_hysteresis'    : '0.800',
             'sensor_name'            : 'DRAM VDD Current',
             'sensor_reading'         : '1.200 (+/- 0) Amps',
             'sensor_type'            : 'Current',
             'status'                 : 'ok',
             'upper_critical'         : '34.200',
             'upper_non_critical'     : '34.200',
             'upper_non_recoverable'  : '34.200'
            },
             ... #
             ... # Output trimmed for brevity ... many more sensors ...
             ... #
         'VCORE Voltage':
             {
              'entity_id'             : '7.1',
              'event_message_control' : 'Per-threshold',
              'lower_critical'        : '1.100',
              'lower_non_critical'    : '1.100',
              'lower_non_recoverable' : '1.100',
              'maximum_sensor_range'  : '0.245',
              'minimum_sensor_range'  : 'Unspecified',
              'negative_hysteresis'   : '0.020',
              'nominal_reading'       : '1.000',
              'normal_maximum'        : '1.410',
              'normal_minimum'        : '0.720',
              'positive_hysteresis'   : '0.020',
              'sensor_name'           : 'VCORE Voltage',
              'sensor_reading'        : '0 (+/- 0) Volts',
              'sensor_type'           : 'Voltage',
              'status'                : 'ok',
              'upper_critical'        : '0.675',
              'upper_non_critical'    : '0.695',
              'upper_non_recoverable' : '0.650'
             }
        }
        >>> # Get ANY sensor name that has the string 'Temp 0' in it ...
        >>> node.get_sensors_dict(search='Temp 0')
        {
         'MP Temp 0':
            {
             'entity_id'              : '7.1',
             'event_message_control'  : 'Per-threshold',
             'lower_critical'         : '2.000',
             'lower_non_critical'     : '5.000',
             'lower_non_recoverable'  : '0.000',
             'maximum_sensor_range'   : 'Unspecified',
             'minimum_sensor_range'   : 'Unspecified',
             'negative_hysteresis'    : '4.000',
             'nominal_reading'        : '25.000',
             'positive_hysteresis'    : '4.000',
             'sensor_name'            : 'MP Temp 0',
             'sensor_reading'         : '0 (+/- 0) degrees C',
             'sensor_type'            : 'Temperature',
             'status'                 : 'ok',
             'upper_critical'         : '70.000',
             'upper_non_critical'     : '55.000',
             'upper_non_recoverable'  : '75.000'
            },
         'TOP Temp 0':
             {
              'entity_id'             : '7.1',
              'event_message_control' : 'Per-threshold',
              'lower_critical'        : '2.000',
              'lower_non_critical'    : '5.000',
              'lower_non_recoverable' : '0.000',
              'maximum_sensor_range'  : 'Unspecified',
              'minimum_sensor_range'  : 'Unspecified',
              'negative_hysteresis'   : '4.000',
              'nominal_reading'       : '25.000',
              'positive_hysteresis'   : '4.000',
              'sensor_name'           : 'TOP Temp 0',
              'sensor_reading'        : '33 (+/- 0) degrees C',
              'sensor_type'           : 'Temperature',
              'status'                : 'ok',
              'upper_critical'        : '70.000',
              'upper_non_critical'    : '55.000',
              'upper_non_recoverable' : '75.000'
             },
         'Temp 0':
             {
              'entity_id'             : '3.1',
              'event_message_control' : 'Per-threshold',
              'lower_critical'        : '2.000',
              'lower_non_critical'    : '5.000',
              'lower_non_recoverable' : '0.000',
              'maximum_sensor_range'  : 'Unspecified',
              'minimum_sensor_range'  : 'Unspecified',
              'negative_hysteresis'   : '4.000',
              'nominal_reading'       : '25.000',
              'positive_hysteresis'   : '4.000',
              'sensor_name'           : 'Temp 0',
              'sensor_reading'        : '0 (+/- 0) degrees C',
              'sensor_type'           : 'Temperature',
              'status'                : 'ok',
              'upper_critical'        : '70.000',
              'upper_non_critical'    : '55.000',
              'upper_non_recoverable' : '75.000'
             }
        }

        .. note::
            * This function is the same as get_sensors(), only a dictionary of
              **{sensor : {attributes :values}}** is returned instead of an
              resultant pyipmi object.

        :param search: Name of the sensor you wish to search for.
        :type search: string

        :return: Sensor information.
        :rtype: dictionary of dictionaries

        """
        return dict((key, vars(value))
                    for key, value in self.get_sensors(search=search).items())

    def get_firmware_info(self):
        """Gets firmware info for each partition on the Node.

        >>> node.get_firmware_info()
        [<pyipmi.fw.FWInfo object at 0x2019850>,
        <pyipmi.fw.FWInfo object at 0x2019b10>,
        <pyipmi.fw.FWInfo object at 0x2019610>, ...]

        :return: Returns a list of FWInfo objects for each
        :rtype: list

        :raises NoFirmwareInfoError: If no fw info exists for any partition.
        :raises IpmiError: If errors in the command occur with BMC communication.

        """
        try:
            fwinfo = [x for x in self.bmc.get_firmware_info()
                      if hasattr(x, "partition")]
            if (len(fwinfo) == 0):
                raise NoFirmwareInfoError("Failed to retrieve firmware info")

            # Clean up the fwinfo results
            for entry in fwinfo:
                if (entry.version == ""):
                    entry.version = "Unknown"

            # Flag CDB as "in use" based on socman info
            for a in range(1, len(fwinfo)):
                previous = fwinfo[a - 1]
                current = fwinfo[a]
                if (current.type.split()[1][1:-1] == "CDB" and
                        current.in_use == "Unknown"):
                    if (previous.type.split()[1][1:-1] != "SOC_ELF"):
                        current.in_use = "1"
                    else:
                        current.in_use = previous.in_use
            return fwinfo
        except IpmiError as error_details:
            raise IpmiError(self._parse_ipmierror(error_details))

    def get_firmware_info_dict(self):
        """Gets firmware info for each partition on the Node.

        .. note::
            * This function is the same as get_firmware_info(), only a
              dictionary of **{attributes : values}** is returned instead of an
              resultant FWInfo object.


        >>> node.get_firmware_info_dict()
        [
            {'daddr'     : '20029000',
             'in_use'    : 'Unknown',
             'partition' : '00',
             'priority'  : '0000000c',
             'version'   : 'v0.9.1',
             'flags'     : 'fffffffd',
             'offset'    : '00000000',
             'type'      : '02 (S2_ELF)',
             'size'      : '00005000'},
             .... # Output trimmed for brevity.
             .... # partitions
             .... # 1 - 16
            {'daddr'     : '20029000',
             'in_use'    : 'Unknown',
             'partition' : '17',
             'priority'  : '0000000b',
             'version'   : 'v0.9.1',
             'flags'     : 'fffffffd',
             'offset'    : '00005000',
             'type'      : '02 (S2_ELF)',
             'size'      : '00005000'}
        ]

        :return: Returns a list of FWInfo objects for each
        :rtype: list

        :raises NoFirmwareInfoError: If no fw info exists for any partition.
        :raises IpmiError: If errors in the command occur with BMC communication.

        """
        return [vars(info) for info in self.get_firmware_info()]

    def is_updatable(self, package, partition_arg="INACTIVE", priority=None):
        """Checks to see if the node can be updated with this firmware package.

        >>> from cxmanage_api.firmware_package import FirmwarePackage
        >>> fwpkg = FirmwarePackage('ECX-1000_update-v1.7.1-dirty.tar.gz')
        >>> fwpkg.version
        'ECX-1000-v1.7.1-dirty'
        >>> node.is_updatable(fwpkg)
        True

        :return: Whether the node is updatable or not.
        :rtype: boolean

        """
        try:
            self._check_firmware(package, partition_arg, priority)
            return True
        except (SocmanVersionError, FirmwareConfigError, PriorityIncrementError,
                NoPartitionError, ImageSizeError, PartitionInUseError):
            return False

    def update_firmware(self, package, partition_arg="INACTIVE",
                          priority=None):
        """ Update firmware on this target.

        >>> from cxmanage_api.firmware_package import FirmwarePackage
        >>> fwpkg = FirmwarePackage('ECX-1000_update-v1.7.1-dirty.tar.gz')
        >>> fwpkg.version
        'ECX-1000-v1.7.1-dirty'
        >>> node.update_firmware(package=fwpkg)

        :param  package: Firmware package to deploy.
        :type package: `FirmwarePackage <firmware_package.html>`_
        :param partition_arg: Partition to upgrade to.
        :type partition_arg: string

        :raises PriorityIncrementError: If the SIMG Header priority cannot be
                                        changed.

        """
        fwinfo = self.get_firmware_info()

        # Get the new priority
        if (priority == None):
            priority = self._get_next_priority(fwinfo, package)

        updated_partitions = []

        for image in package.images:
            if (image.type == "UBOOTENV"):
                # Get partitions
                running_part = self._get_partition(fwinfo, image.type, "FIRST")
                factory_part = self._get_partition(fwinfo, image.type,
                        "SECOND")

                # Update factory ubootenv
                self._upload_image(image, factory_part, priority)

                # Update running ubootenv
                old_ubootenv_image = self._download_image(running_part)
                old_ubootenv = self.ubootenv(open(
                                        old_ubootenv_image.filename).read())
                try:
                    ubootenv = self.ubootenv(open(image.filename).read())
                    ubootenv.set_boot_order(old_ubootenv.get_boot_order())

                    filename = temp_file()
                    with open(filename, "w") as f:
                        f.write(ubootenv.get_contents())
                    ubootenv_image = self.image(filename, image.type, False,
                                           image.daddr, image.skip_crc32,
                                           image.version)
                    self._upload_image(ubootenv_image, running_part,
                            priority)
                except (ValueError, Exception):
                    self._upload_image(image, running_part, priority)

                updated_partitions += [running_part, factory_part]
            else:
                # Get the partitions
                if (partition_arg == "BOTH"):
                    partitions = [self._get_partition(fwinfo, image.type,
                            "FIRST"), self._get_partition(fwinfo, image.type,
                            "SECOND")]
                else:
                    partitions = [self._get_partition(fwinfo, image.type,
                            partition_arg)]

                # Update the image
                for partition in partitions:
                    self._upload_image(image, partition, priority)

                updated_partitions += partitions

        if package.version:
            self.bmc.set_firmware_version(package.version)

        # Post verify
        fwinfo = self.get_firmware_info()
        for old_partition in updated_partitions:
            partition_id = int(old_partition.partition)
            new_partition = fwinfo[partition_id]

            if new_partition.type != old_partition.type:
                raise Exception("Update failed (partition %i, type changed)"
                        % partition_id)

            if int(new_partition.priority, 16) != priority:
                raise Exception("Update failed (partition %i, wrong priority)"
                        % partition_id)

            if int(new_partition.flags, 16) & 2 != 0:
                raise Exception("Update failed (partition %i, not activated)"
                        % partition_id)

            result = self.bmc.check_firmware(partition_id)
            if not hasattr(result, "crc32") or result.error != None:
                raise Exception("Update failed (partition %i, post-crc32 fail)"
                        % partition_id)


    def config_reset(self):
        """Resets configuration to factory defaults.

        >>> node.config_reset()

        :raises IpmiError: If errors in the command occur with BMC communication.
        :raises Exception: If there are errors within the command response.

        """
        try:
            # Reset CDB
            result = self.bmc.reset_firmware()
            if (hasattr(result, "error")):
                raise Exception(result.error)

            # Reset ubootenv
            fwinfo = self.get_firmware_info()
            running_part = self._get_partition(fwinfo, "UBOOTENV", "FIRST")
            factory_part = self._get_partition(fwinfo, "UBOOTENV", "SECOND")
            image = self._download_image(factory_part)
            self._upload_image(image, running_part)
            # Clear SEL
            self.bmc.sel_clear()
        except IpmiError as e:
            raise IpmiError(self._parse_ipmierror(e))

    def set_boot_order(self, boot_args):
        """Sets boot-able device order for this node.

        >>> node.set_boot_order(boot_args=['pxe', 'disk'])

        :param boot_args: Arguments list to pass on to the uboot environment.
        :type boot_args: list

        """
        fwinfo = self.get_firmware_info()
        first_part = self._get_partition(fwinfo, "UBOOTENV", "FIRST")
        active_part = self._get_partition(fwinfo, "UBOOTENV", "ACTIVE")

        # Download active ubootenv, modify, then upload to first partition
        image = self._download_image(active_part)
        ubootenv = self.ubootenv(open(image.filename).read())
        ubootenv.set_boot_order(boot_args)
        priority = max(int(x.priority, 16) for x in [first_part, active_part])

        filename = temp_file()
        with open(filename, "w") as f:
            f.write(ubootenv.get_contents())

        ubootenv_image = self.image(filename, image.type, False, image.daddr,
                                    image.skip_crc32, image.version)
        self._upload_image(ubootenv_image, first_part, priority)

    def get_boot_order(self):
        """Returns the boot order for this node.

        >>> node.get_boot_order()
        ['pxe', 'disk']

        """
        return self.get_ubootenv().get_boot_order()

    def get_versions(self):
        """Get version info from this node.

        >>> node.get_versions()
        <pyipmi.info.InfoBasicResult object at 0x2019b90>
        >>> # Some useful information ...
        >>> info.a9boot_version
        'v2012.10.16'
        >>> info.cdb_version
        'v0.9.1'

        :returns: The results of IPMI info basic command.
        :rtype: pyipmi.info.InfoBasicResult

        :raises IpmiError: If errors in the command occur with BMC communication.
        :raises Exception: If there are errors within the command response.

        """
        try:
            result = self.bmc.get_info_basic()
        except IpmiError as e:
            raise IpmiError(self._parse_ipmierror(e))

        fwinfo = self.get_firmware_info()
        components = [("cdb_version", "CDB"),
                      ("stage2_version", "S2_ELF"),
                      ("bootlog_version", "BOOT_LOG"),
                      ("a9boot_version", "A9_EXEC"),
                      ("uboot_version", "A9_UBOOT"),
                      ("ubootenv_version", "UBOOTENV"),
                      ("dtb_version", "DTB")]
        for var, ptype in components:
            try:
                partition = self._get_partition(fwinfo, ptype, "ACTIVE")
                setattr(result, var, partition.version)
            except NoPartitionError:
                pass
        try:
            card = self.bmc.get_info_card()
            setattr(result, "hardware_version", "%s X%02i" %
                    (card.type, int(card.revision)))
        except IpmiError as err:
            if (self.verbose):
                print str(err)
            # Should raise an error, but we want to allow the command
            # to continue gracefully if the ECME is out of date.
            setattr(result, "hardware_version", "Unknown")
        return result

    def get_versions_dict(self):
        """Get version info from this node.

        .. note::
            * This function is the same as get_versions(), only a dictionary of
              **{attributes : values}** is returned instead of an resultant
              pyipmi object.

        >>> n.get_versions_dict()
        {'soc_version'      : 'v0.9.1',
         'build_number'     : '7E10987C',
         'uboot_version'    : 'v2012.07_cx_2012.10.29',
         'ubootenv_version' : 'v2012.07_cx_2012.10.29',
         'timestamp'        : '1352911670',
         'cdb_version'      : 'v0.9.1-39-g7e10987',
         'header'           : 'Calxeda SoC (0x0096CD)',
         'version'          : 'ECX-1000-v1.7.1',
         'bootlog_version'  : 'v0.9.1-39-g7e10987',
         'a9boot_version'   : 'v2012.10.16',
         'stage2_version'   : 'v0.9.1',
         'dtb_version'      : 'v3.6-rc1_cx_2012.10.02',
         'card'             : 'EnergyCard X02'
        }

        :returns: The results of IPMI info basic command.
        :rtype: dictionary

        :raises IpmiError: If errors in the command occur with BMC communication.
        :raises Exception: If there are errors within the command response.

        """
        return vars(self.get_versions())

    def ipmitool_command(self, ipmitool_args):
        """Send a raw ipmitool command to the node.

        >>> node.ipmitool_command(['cxoem', 'info', 'basic'])
        'Calxeda SoC (0x0096CD)\\n  Firmware Version: ECX-1000-v1.7.1-dirty\\n
        SoC Version: 0.9.1\\n  Build Number: A69523DC \\n
        Timestamp (1351543656): Mon Oct 29 15:47:36 2012'

        :param ipmitool_args: Arguments to pass to the ipmitool.
        :type ipmitool_args: list

        """
        if ("IPMITOOL_PATH" in os.environ):
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

    def get_ubootenv(self):
        """Get the active u-boot environment.

        >>> node.get_ubootenv()
        <cxmanage_api.ubootenv.UbootEnv instance at 0x209da28>

        :return: U-Boot Environment object.
        :rtype: `UBootEnv <ubootenv.html>`_

        """
        fwinfo = self.get_firmware_info()
        partition = self._get_partition(fwinfo, "UBOOTENV", "ACTIVE")
        image = self._download_image(partition)
        return self.ubootenv(open(image.filename).read())

    def get_fabric_ipinfo(self):
        """Gets what ip information THIS node knows about the Fabric.

        >>> node.get_fabric_ipinfo()
        {0: '10.20.1.9', 1: '10.20.2.131', 2: '10.20.0.220', 3: '10.20.2.5'}

        :return: Returns a map of node_ids->ip_addresses.
        :rtype: dictionary

        :raises IpmiError: If the IPMI command fails.
        :raises TftpException: If the TFTP transfer fails.

        """
        try:
            filename = self._run_fabric_command(
                function_name='fabric_config_get_ip_info',
            )
        except IpmiError as e:
            raise IpmiError(self._parse_ipmierror(e))

        # Parse addresses from ipinfo file
        results = {}
        for line in open(filename):
            if (line.startswith("Node")):
                elements = line.split()
                node_id = int(elements[1].rstrip(":"))
                node_ip_address = elements[2]

                # Old boards used to return 0.0.0.0 sometimes -- might not be
                # an issue anymore.
                if (node_ip_address != "0.0.0.0"):
                    results[node_id] = node_ip_address

        # Make sure we found something
        if (not results):
            raise TftpException("Node failed to reach TFTP server")

        return results

    def get_fabric_macaddrs(self):
        """Gets what macaddr information THIS node knows about the Fabric.

        :return: Returns a map of node_ids->ports->mac_addresses.
        :rtype: dictionary

        :raises IpmiError: If the IPMI command fails.
        :raises TftpException: If the TFTP transfer fails.

        """
        try:
            filename = self._run_fabric_command(
                function_name='fabric_config_get_mac_addresses'
            )

        except IpmiError as e:
            raise IpmiError(self._parse_ipmierror(e))

        # Parse addresses from ipinfo file
        results = {}
        for line in open(filename):
            if (line.startswith("Node")):
                elements = line.split()
                node_id = int(elements[1].rstrip(","))
                port = int(elements[3].rstrip(":"))
                mac_address = elements[4]

                if not node_id in results:
                    results[node_id] = {}
                if not port in results[node_id]:
                    results[node_id][port] = []
                results[node_id][port].append(mac_address)

        # Make sure we found something
        if (not results):
            raise TftpException("Node failed to reach TFTP server")

        return results

    def get_fabric_uplink_info(self):
        """Gets what uplink information THIS node knows about the Fabric.

        >>> node.get_fabric_uplink_info()
        {'0': {'eth0': '0', 'eth1': '0', 'mgmt': '0'},
         '1': {'eth0': '0', 'eth1': '0', 'mgmt': '0'},
         '2': {'eth0': '0', 'eth1': '0', 'mgmt': '0'},
         '3': {'eth0': '0', 'eth1': '0', 'mgmt': '0'},
         '4': {'eth0': '0', 'eth1': '0', 'mgmt': '0'}}

        :return: Returns a map of {node_id : {interface : uplink}}
        :rtype: dictionary

        :raises IpmiError: If the IPMI command fails.
        :raises TftpException: If the TFTP transfer fails.

        """
        filename = self._run_fabric_command(
            function_name='fabric_config_get_uplink_info'
        )

        # Parse addresses from ipinfo file
        results = {}
        for line in open(filename):
            node_id = int(line.replace('Node ', '')[0])
            ul_info = line.replace('Node %s:' % node_id, '').strip().split(',')
            node_data = {}
            for ul in ul_info:
                data = tuple(ul.split())
                node_data[data[0]] = int(data[1])
            results[node_id] = node_data

        # Make sure we found something
        if (not results):
            raise TftpException("Node failed to reach TFTP server")

        return results

    def get_link_stats(self, link=0):
        """Gets the linkstats for the link specified.

        :param link: The link to get stats for (0-4).
        :type link: integer

        :returns: The linkstats for the link specified.
        :rtype: dictionary

        :raises IpmiError: If the IPMI command fails.

        """
        filename = self._run_fabric_command(
            function_name='fabric_get_linkstats',
            link=link
        )
        results = {}
        for line in open(filename):
            if ('=' in line):
                reg_value = line.strip().split('=')
                if (len(reg_value) < 2):
                    raise ValueError(
                        'Register: %s has no value!' % reg_value[0]
                    )
                else:
                    results[
                        reg_value[0].replace(
                            'pFS_LCn', 'FS_LC%s' % link
                        ).replace('(link)', '').strip()
                    ] = reg_value[1].strip()

        # Make sure we found something
        if (not results):
            raise TftpException("Node failed to reach TFTP server")

        return results

    def get_linkmap(self):
        """Gets the src and destination of each link on a node.

        :return: Returns a map of link_id->node_id.
        :rtype: dictionary

        :raises IpmiError: If the IPMI command fails.
        :raises TftpException: If the TFTP transfer fails.

        """
        try:
            filename = self._run_fabric_command(
                function_name='fabric_info_get_link_map',
            )
        except IpmiError as e:
            raise IpmiError(self._parse_ipmierror(e))

        results = {}
        for line in open(filename):
            if (line.startswith("Link")):
                elements = line.strip().split()
                link_id = int(elements[1].rstrip(':'))
                node_id = int(elements[3].strip())
                results[link_id] = node_id

        # Make sure we found something
        if (not results):
            raise TftpException("Node failed to reach TFTP server")

        return results

    def get_routing_table(self):
        """Gets the routing table as instantiated in the fabric switch.

        :return: Returns a map of node_id->rt_entries.
        :rtype: dictionary

        :raises IpmiError: If the IPMI command fails.
        :raises TftpException: If the TFTP transfer fails.

        """
        try:
            filename = self._run_fabric_command(
                function_name='fabric_info_get_routing_table',
            )
        except IpmiError as e:
            raise IpmiError(self._parse_ipmierror(e))

        results = {}
        for line in open(filename):
            if (line.startswith("Node")):
                elements = line.strip().split()
                node_id = int(elements[1].rstrip(':'))
                rt_entries = []
                for entry in elements[4].strip().split('.'):
                    rt_entries.append(int(entry))
                results[node_id] = rt_entries

        # Make sure we found something
        if (not results):
            raise TftpException("Node failed to reach TFTP server")

        return results

    def get_depth_chart(self):
        """Gets a table indicating the distance from a given node to all other
        nodes on each fabric link.

        :return: Returns a map of target->(neighbor, hops),
                                  [other (neighbors,hops)]
        :rtype: dictionary

        :raises IpmiError: If the IPMI command fails.
        :raises TftpException: If the TFTP transfer fails.

        """
        try:
            filename = self._run_fabric_command(
                function_name='fabric_info_get_depth_chart',
            )
        except IpmiError as e:
            raise IpmiError(self._parse_ipmierror(e))

        results = {}
        for line in open(filename):
            if (line.startswith("Node")):
                elements = line.strip().split()
                target = int(elements[1].rstrip(':'))
                neighbor = int(elements[8].rstrip(':'))
                hops = int(elements[4].strip())
                dchrt_entries = {}
                dchrt_entries['shortest'] = (neighbor, hops)
                try:
                    other_hops_neighbors = elements[12].strip().split('[,\s]+')
                    hops = []
                    for entry in other_hops_neighbors:
                        pair = entry.strip().split('/')
                        hops.append((int(pair[1]), int(pair[0])))
                    dchrt_entries['others'] = hops
                except:
                    pass

                results[target] = dchrt_entries

        # Make sure we found something
        if (not results):
            raise TftpException("Node failed to reach TFTP server")

        return results

    def get_server_ip(self, interface=None, ipv6=False, user="user1",
            password="1Password", aggressive=False):
        """Get the IP address of the Linux server. The server must be powered
        on for this to work.

        >>> node.get_server_ip()
        '192.168.100.100'

        :param interface: Network interface to check (e.g. eth0).
        :type interface: string
        :param ipv6: Return an IPv6 address instead of IPv4.
        :type ipv6: boolean
        :param user: Linux username.
        :type user: string
        :param password: Linux password.
        :type password: string
        :param aggressive: Discover the IP aggressively (may power cycle node).
        :type aggressive: boolean

        :return: The IP address of the server.
        :rtype: string
        :raises IpmiError: If errors in the command occur with BMC communication.
        :raises IPDiscoveryError: If the server is off, or the IP can't be obtained.

        """
        verbosity = 2 if self.verbose else 0
        retriever = self.ipretriever(self.ip_address, aggressive=aggressive,
                verbosity=verbosity, server_user=user, server_password=password,
                interface=interface, ipv6=ipv6, bmc=self.bmc)
        retriever.run()
        return retriever.server_ip

    def get_linkspeed(self, link=None, actual=False):
        """Get the linkspeed for the node.  This returns either
        the actual linkspeed based on phy controller register settings,
        or if sent to a primary node, the linkspeed setting for the
        Profile 0 of the currently active Configuration.

        >>> fabric.get_linkspeed()
        2.5

        :param link: The fabric link number to read the linkspeed for.
        :type link: integer
        :param actual: WhetherThe fabric link number to read the linkspeed for.
        :type actual: boolean

        :return: Linkspeed for the fabric..
        :rtype: float

        """
        try:
            return self.bmc.fabric_get_linkspeed(link=link, actual=actual)
        except IpmiError as e:
            raise IpmiError(self._parse_ipmierror(e))

    def get_uplink(self, iface=0):
        """Get the uplink a MAC will use when transmitting a packet out of the
        cluster.

        >>> fabric.get_uplink(iface=1)
        0

        :param iface: The interface for the uplink.
        :type iface: integer

        :return: The uplink iface is connected to.
        :rtype: integer

        :raises IpmiError: When any errors are encountered.

        """
        try:
            return self.bmc.fabric_config_get_uplink(iface=iface)
        except IpmiError as e:
            raise IpmiError(self._parse_ipmierror(e))

    def set_uplink(self, uplink=0, iface=0):
        """Set the uplink a MAC will use when transmitting a packet out of the
        cluster.

        >>> #
        >>> # Set eth0 to uplink 1 ...
        >>> #
        >>> fabric.set_uplink(uplink=1,iface=0)

        :param uplink: The uplink to set.
        :type uplink: integer
        :param iface: The interface for the uplink.
        :type iface: integer

        :raises IpmiError: When any errors are encountered.

        """
        try:
            return self.bmc.fabric_config_set_uplink(
                uplink=uplink,
                iface=iface
            )
        except IpmiError as e:
            raise IpmiError(self._parse_ipmierror(e))

    def _run_fabric_command(self, function_name, **kwargs):
        """Handles the basics of sending a node a command for fabric data."""
        filename = temp_file()
        basename = os.path.basename(filename)
        try:
            getattr(self.bmc, function_name)(filename=basename, **kwargs)
            self.ecme_tftp.get_file(basename, filename)

        except (IpmiError, TftpException) as e:
            try:
                getattr(self.bmc, function_name)(
                    filename=basename,
                    tftp_addr=self.tftp_address,
                    **kwargs
                )

            except IpmiError as e:
                raise IpmiError(self._parse_ipmierror(e))

            deadline = time.time() + 10
            while (time.time() < deadline):
                try:
                    time.sleep(1)
                    self.tftp.get_file(src=basename, dest=filename)
                    if (os.path.getsize(filename) > 0):
                        break

                except (TftpException, IOError):
                    pass

        return filename

    def _get_partition(self, fwinfo, image_type, partition_arg):
        """Get a partition for this image type based on the argument."""
        # Filter partitions for this type
        partitions = [x for x in fwinfo if
                      x.type.split()[1][1:-1] == image_type]
        if (len(partitions) < 1):
            raise NoPartitionError("No partition of type %s found on host"
                    % image_type)

        if (partition_arg == "FIRST"):
            return partitions[0]
        elif (partition_arg == "SECOND"):
            if (len(partitions) < 2):
                raise NoPartitionError("No second partition found on host")
            return partitions[1]
        elif (partition_arg == "OLDEST"):
            # Return the oldest partition
            partitions.sort(key=lambda x: x.partition, reverse=True)
            partitions.sort(key=lambda x: x.priority)
            return partitions[0]
        elif (partition_arg == "NEWEST"):
            # Return the newest partition
            partitions.sort(key=lambda x: x.partition)
            partitions.sort(key=lambda x: x.priority, reverse=True)
            return partitions[0]
        elif (partition_arg == "INACTIVE"):
            # Return the partition that's not in use (or least likely to be)
            partitions.sort(key=lambda x: x.partition, reverse=True)
            partitions.sort(key=lambda x: x.priority)
            partitions.sort(key=lambda x: int(x.flags, 16) & 2 == 0)
            partitions.sort(key=lambda x: x.in_use == "1")
            return partitions[0]
        elif (partition_arg == "ACTIVE"):
            # Return the partition that's in use (or most likely to be)
            partitions.sort(key=lambda x: x.partition)
            partitions.sort(key=lambda x: x.priority, reverse=True)
            partitions.sort(key=lambda x: int(x.flags, 16) & 2 == 1)
            partitions.sort(key=lambda x: x.in_use == "0")
            return partitions[0]
        else:
            raise ValueError("Invalid partition argument: %s" % partition_arg)

    def _upload_image(self, image, partition, priority=None):
        """Upload a single image. This includes uploading the image, performing
        the firmware update, crc32 check, and activation.
        """
        partition_id = int(partition.partition)
        if (priority == None):
            priority = int(partition.priority, 16)
        daddr = int(partition.daddr, 16)

        # Check image size
        if (image.size() > int(partition.size, 16)):
            raise ImageSizeError("%s image is too large for partition %i" %
                    (image.type, partition_id))

        filename = image.render_to_simg(priority, daddr)
        basename = os.path.basename(filename)

        try:
            self.bmc.register_firmware_write(basename, partition_id, image.type)
            self.ecme_tftp.put_file(filename, basename)
        except (IpmiError, TftpException):
            # Fall back and use TFTP server
            self.tftp.put_file(filename, basename)
            result = self.bmc.update_firmware(basename, partition_id,
                    image.type, self.tftp_address)
            if (not hasattr(result, "tftp_handle_id")):
                raise AttributeError("Failed to start firmware upload")
            self._wait_for_transfer(result.tftp_handle_id)

        # Verify crc and activate
        result = self.bmc.check_firmware(partition_id)
        if ((not hasattr(result, "crc32")) or (result.error != None)):
            raise AttributeError("Node reported crc32 check failure")
        self.bmc.activate_firmware(partition_id)

    def _download_image(self, partition):
        """Download an image from the target."""
        filename = temp_file()
        basename = os.path.basename(filename)
        partition_id = int(partition.partition)
        image_type = partition.type.split()[1][1:-1]

        try:
            self.bmc.register_firmware_read(basename, partition_id, image_type)
            self.ecme_tftp.get_file(basename, filename)
        except (IpmiError, TftpException):
            # Fall back and use TFTP server
            result = self.bmc.retrieve_firmware(basename, partition_id,
                    image_type, self.tftp_address)
            if (not hasattr(result, "tftp_handle_id")):
                raise AttributeError("Failed to start firmware download")
            self._wait_for_transfer(result.tftp_handle_id)
            self.tftp.get_file(basename, filename)

        return self.image(filename=filename, image_type=image_type,
                          daddr=int(partition.daddr, 16),
                          version=partition.version)

    def _wait_for_transfer(self, handle):
        """Wait for a firmware transfer to finish."""
        deadline = time.time() + 180
        result = self.bmc.get_firmware_status(handle)
        if (not hasattr(result, "status")):
            raise AttributeError('Failed to retrieve firmware transfer status')

        while (result.status == "In progress"):
            if (time.time() >= deadline):
                raise TimeoutError("Transfer timed out after 3 minutes")
            time.sleep(1)
            result = self.bmc.get_firmware_status(handle)
            if (not hasattr(result, "status")):
                raise AttributeError(
                        "Failed to retrieve firmware transfer status")

        if (result.status != "Complete"):
            raise TransferFailure("Node reported TFTP transfer failure")

    def _check_firmware(self, package, partition_arg="INACTIVE", priority=None):
        """Check if this host is ready for an update."""
        info = self.get_versions()
        fwinfo = self.get_firmware_info()

        # Check firmware version
        if package.version and info.firmware_version:
            package_match = re.match("^ECX-[0-9]+", package.version)
            firmware_match = re.match("^ECX-[0-9]+", info.firmware_version)
            if package_match and firmware_match:
                package_version = package_match.group(0)
                firmware_version = firmware_match.group(0)
                if package_version != firmware_version:
                    raise FirmwareConfigError(
                            "Refusing to upload an %s package to an %s host"
                            % (package_version, firmware_version))

        # Check socman version
        if (package.required_socman_version):
            ecme_version = info.ecme_version.lstrip("v")
            required_version = package.required_socman_version.lstrip("v")
            if ((package.required_socman_version and
                 parse_version(ecme_version)) <
                 parse_version(required_version)):
                raise SocmanVersionError(
                        "Update requires socman version %s (found %s)"
                        % (required_version, ecme_version))

        # Check slot0 vs. slot2
        # TODO: remove this check
        if (package.config and info.firmware_version != "Unknown" and
                len(info.firmware_version) < 32):
            if "slot2" in info.firmware_version:
                firmware_config = "slot2"
            else:
                firmware_config = "default"

            if (package.config != firmware_config):
                raise FirmwareConfigError(
                        "Refusing to upload a \'%s\' package to a \'%s\' host"
                        % (package.config, firmware_config))

        # Check that the priority can be bumped
        if (priority == None):
            priority = self._get_next_priority(fwinfo, package)

        # Check partitions
        for image in package.images:
            if ((image.type == "UBOOTENV") or (partition_arg == "BOTH")):
                partitions = [self._get_partition(fwinfo, image.type, x)
                        for x in ["FIRST", "SECOND"]]
            else:
                partitions = [self._get_partition(fwinfo, image.type,
                        partition_arg)]

            for partition in partitions:
                if (image.size() > int(partition.size, 16)):
                    raise ImageSizeError(
                            "%s image is too large for partition %i"
                            % (image.type, int(partition.partition)))

                if (image.type in ["CDB", "BOOT_LOG"] and
                        partition.in_use == "1"):
                    raise PartitionInUseError(
                            "Can't upload to a CDB/BOOT_LOG partition that's in use")

        return True

    def _get_next_priority(self, fwinfo, package):
        """ Get the next priority """
        priority = None
        image_types = [x.type for x in package.images]
        for partition in fwinfo:
            partition_active = int(partition.flags, 16) & 2
            partition_type = partition.type.split()[1].strip("()")
            if ((not partition_active) and (partition_type in image_types)):
                priority = max(priority, int(partition.priority, 16) + 1)
        if (priority > 0xFFFF):
            raise PriorityIncrementError(
                            "Unable to increment SIMG priority, too high")
        return priority

    def _parse_ipmierror(self, error_details):
        """Parse a meaningful message from an IpmiError """
        try:
            error = str(error_details).lstrip().splitlines()[0].rstrip()
            if (error.startswith('Error: ')):
                error = error[7:]
            return error
        except IndexError:
            return 'Unknown IPMItool error.'


# End of file: ./node.py

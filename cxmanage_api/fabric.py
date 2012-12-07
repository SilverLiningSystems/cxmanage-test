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

from cxmanage_api.tasks import DEFAULT_TASK_QUEUE
from cxmanage_api.tftp import InternalTftp
from cxmanage_api.node import Node as NODE
from cxmanage_api.cx_exceptions import CommandFailedError


class Fabric(object):
    """ The Fabric class provides management of multiple nodes.

    >>> from cxmanage_api.fabric import Fabric
    >>> fabric = Fabric('10.20.1.9')

    :param ip_address: The ip_address of ANY known node for the Fabric.
    :type ip_address: string
    :param username: The login username credential. [Default admin]
    :type username: string
    :param password: The login password credential. [Default admin]
    :type password: string
    :param verbose: Flag to turn on verbose output (cmd/response).
    :type verbose: boolean
    :param node: Node type, for dependency integration.
    :type node: `Node <node.html>`_
    """

    def __init__(self, ip_address, username="admin", password="admin",
                  tftp=None, task_queue=DEFAULT_TASK_QUEUE, verbose=False,
                  node=None):
        """Default constructor for the Fabric class."""
        self.ip_address = ip_address
        self.username = username
        self.password = password
        self._tftp = tftp
        self.task_queue = task_queue
        self.verbose = verbose
        self.node = node

        self._nodes = {}

        if (not self.node):
            self.node = NODE

        if (not self._tftp):
            self._tftp = InternalTftp()

    def __eq__(self, other):
        """__eq__() override."""
        return (isinstance(other, Fabric) and self.nodes == other.nodes)

    def __hash__(self):
        """__hash__() override."""
        return hash(tuple(self.nodes.iteritems()))

    @property
    def tftp(self):
        """Returns the tftp server for this Fabric.

        >>> fabric.tftp
        <cxmanage_api.tftp.InternalTftp object at 0x7f5ebbd20b10>

        :return: The tftfp server.
        :rtype: `Tftp <tftp.html>`_

        """
        return self._tftp

    @tftp.setter
    def tftp(self, value):
        self._tftp = value

        if not self._nodes:
            return

        for node in self.nodes.values():
            node.tftp = value

    @property
    def nodes(self):
        """List of nodes in this fabric.

        >>> fabric.nodes
        {
         0: <cxmanage_api.node.Node object at 0x2052710>,
         1: <cxmanage_api.node.Node object at 0x2052790>,
         2: <cxmanage_api.node.Node object at 0x2052850>,
         3: <cxmanage_api.node.Node object at 0x2052910>
        }

        .. note::
            * Fabric nodes are lazily initialized.

        :returns: A mapping of node ids to node objects.
        :rtype: dictionary

        """
        if not self._nodes:
            self._discover_nodes(self.ip_address)
        return self._nodes

    def get_mac_addresses(self, async=False):
        """Gets MAC addresses from all nodes.

        >>> fabric.get_mac_addresses()
        {
         0: ['fc:2f:40:3b:ec:40', 'fc:2f:40:3b:ec:41', 'fc:2f:40:3b:ec:42'],
         1: ['fc:2f:40:91:dc:40', 'fc:2f:40:91:dc:41', 'fc:2f:40:91:dc:42'],
         2: ['fc:2f:40:ab:f7:14', 'fc:2f:40:ab:f7:15', 'fc:2f:40:ab:f7:16'],
         3: ['fc:2f:40:88:b3:6c', 'fc:2f:40:88:b3:6d', 'fc:2f:40:88:b3:6e']
        }

        :param async: Flag that determines if the command result (dictionary)
                      is returned or a Task object (can get status, etc.).
        :type async: boolean

        :return: The MAC addresses for each node.
        :rtype: dictionary or `Task <tasks.html>`_

        """
        return self._run_command(async, "get_mac_addresses")

    def get_power(self, async=False):
        """Returns the power status for all nodes.

        >>> fabric.get_power()
        {0: False, 1: False, 2: False, 3: False}

        :param async: Flag that determines if the command result (dictionary)
                      is returned or a Command object (for cmd status, etc.).
        :type async: boolean

        :return: The power status of each node.
        :rtype: dictionary or `Task <tasks.html>`_

        """
        return self._run_command(async, "get_power")

    def set_power(self, mode, async=False):
        """Send an IPMI power command to all nodes.

        >>> # On ...
        >>> fabric.set_power(mode='on')
        >>> # Off ...
        >>> fabric.set_power(mode='off')
        >>> # Sanity check ...
        >>> fabric.get_power()
        {0: False, 1: False, 2: False, 3: False}

        :param mode: Mode to set the power to (for all nodes).
        :type mode: string
        :param async: Flag that determines if the command result (dictionary)
                      is returned or a Command object (can get status, etc.).
        :type async: boolean

        """
        self._run_command(async, "set_power", mode)

    def get_power_policy(self, async=False):
        """Gets the power policy from all nodes.

        >>> fabric.get_power_policy()
        {0: 'always-on', 1: 'always-on', 2: 'always-on', 3: 'always-on'}

        :param async: Flag that determines if the command result (dictionary)
                      is returned or a Command object (can get status, etc.).
        :type async: boolean

        :return: The power policy for all nodes on this fabric.
        :rtype: dictionary or `Task <tasks.html>`_

        """
        return self._run_command(async, "get_power_policy")

    def set_power_policy(self, state, async=False):
        """Sets the power policy on all nodes.

        >>> fabric.set_power_policy(state='always-off')
        >>> # Check to see if it took ...
        >>> fabric.get_power_policy()
        {0: 'always-off', 1: 'always-off', 2: 'always-off', 3: 'always-off'}

        :param state: State to set the power policy to for all nodes.
        :type state: string
        :param async: Flag that determines if the command result (dictionary)
                      is returned or a Command object (can get status, etc.).
        :type async: boolean

        """
        self._run_command(async, "set_power_policy", state)

    def mc_reset(self, async=False):
        """Resets the management controller on all nodes.

        >>> fabric.mc_reset()

        :param async: Flag that determines if the command result (dictionary)
                      is returned or a Command object (can get status, etc.).
        :type async: boolean

        """
        self._run_command(async, "mc_reset")

    def get_sensors(self, search="", async=False):
        """Gets sensors from all nodes.

        >>> fabric.get_sensors()
        {
         0: {
             'DRAM VDD Current' : <pyipmi.sdr.AnalogSdr object at 0x1a1eb50>,
             'DRAM VDD Voltage' : <pyipmi.sdr.AnalogSdr object at 0x1a1ef10>,
             'MP Temp 0'        : <pyipmi.sdr.AnalogSdr object at 0x1a1ec90>,
             'Node Power'       : <pyipmi.sdr.AnalogSdr object at 0x1a1ed90>,
             'TOP Temp 0'       : <pyipmi.sdr.AnalogSdr object at 0x1a1ecd0>,
             'TOP Temp 1'       : <pyipmi.sdr.AnalogSdr object at 0x1a1ed50>,
             'TOP Temp 2'       : <pyipmi.sdr.AnalogSdr object at 0x1a1edd0>,
             'Temp 0'           : <pyipmi.sdr.AnalogSdr object at 0x1a1ead0>,
             'Temp 1'           : <pyipmi.sdr.AnalogSdr object at 0x1a1ebd0>,
             'Temp 2'           : <pyipmi.sdr.AnalogSdr object at 0x1a1ec10>,
             'Temp 3'           : <pyipmi.sdr.AnalogSdr object at 0x1a1ec50>,
             'V09 Current'      : <pyipmi.sdr.AnalogSdr object at 0x1a1ef90>,
             'V09 Voltage'      : <pyipmi.sdr.AnalogSdr object at 0x1a1ee90>,
             'V18 Current'      : <pyipmi.sdr.AnalogSdr object at 0x1a1ef50>,
             'V18 Voltage'      : <pyipmi.sdr.AnalogSdr object at 0x1a1ee50>,
             'VCORE Current'    : <pyipmi.sdr.AnalogSdr object at 0x1a1efd0>,
             'VCORE Power'      : <pyipmi.sdr.AnalogSdr object at 0x1a1ee10>,
             'VCORE Voltage'    : <pyipmi.sdr.AnalogSdr object at 0x1a1eed0>
            },
            #
            # Output trimmed for brevity ... The output would be the same
            # (format) for the remaining 3 ECMEs on this system.
            #
        },

        .. note::
            * Output condensed for brevity.
            * If the name parameter is not specified, all sensors are returned.

        :param name: Name of the sensor to get. (for all nodes)
        :type name: string
        :param async: Flag that determines if the command result (dictionary)
                      is returned or a Command object (can get status, etc.).
        :type async: boolean

        """
        return self._run_command(async, "get_sensors", search)

    def get_firmware_info(self, async=False):
        """Gets the firmware info from all nodes.

        >>> fabric.get_firmware_info()
        {
         0: [<pyipmi.fw.FWInfo object at 0x2808110>, ...],
         1: [<pyipmi.fw.FWInfo object at 0x28080d0>, ...],
         2: [<pyipmi.fw.FWInfo object at 0x2808090>, ...],
         3: [<pyipmi.fw.FWInfo object at 0x7f35540660d0>, ...]
        }

        :param async: Flag that determines if the command result (dictionary)
                      is returned or a Command object (can get status, etc.).
        :type async: boolean

        :return: THe firmware info for all nodes.
        :rtype: dictionary or `Task <tasks.html>`_

        """
        return self._run_command(async, "get_firmware_info")

    def get_firmware_info_dict(self, async=False):
        """Gets the firmware info from all nodes.

        >>> fabric.get_firmware_info_dict()
        {0:
           [
            #
            # Each dictionary (in order) in this list represents the
            # corresponding partition information
            #
             {# Partition 0
              'daddr'     : '20029000',
              'flags'     : 'fffffffd',
              'in_use'    : 'Unknown',
              'offset'    : '00000000',
              'partition' : '00',
              'priority'  : '0000000c',
              'size'      : '00005000',
              'type'      : '02 (S2_ELF)',
              'version'   : 'v0.9.1'
             },
             # Partitions 1 - 17
           ],
         #
         # Output trimmed for brevity ... The remaining Nodes in the Fabric
         # would display all the partition format in the same manner.
         #
        }

        :param async: Flag that determines if the command result (dictionary)
                      is returned or a Command object (can get status, etc.).
        :type async: boolean

        :return: THe firmware info for all nodes.
        :rtype: dictionary or `Task <tasks.html>`_

        """
        results = {}
        for node_number, info in self.get_firmware_info(async=async).items():
            results[node_number] = [vars(partition) for partition in info]
        return results

    def is_updatable(self, package, partition_arg="INACTIVE", priority=None,
                       async=False):
        """Checks to see if all nodes can be updated with this fw package.

        >>> fabric.is_updatable(package=fwpkg)
        {0: True, 1: True, 2: True, 3: True}

        :param package: Firmware package to test for updating.
        :type package: `FirmwarePackage <firmware_package.html>`_
        :param partition: Partition to test for updating.
        :type partition: string
        :param priority: SIMG Header priority.
        :type priority: integer
        :param async: Flag that determines if the command result (dictionary)
                      is returned or a Command object (can get status, etc.).
        :type async: boolean

        :return: Whether or not a node can be updated with the specified
                 firmware package.
        :rtype: dictionary or `Task <tasks.html>`_

        """
        return self._run_command(async, "is_updatable", package,
                                 partition_arg, priority)

    def update_firmware(self, package, partition_arg="INACTIVE",
                          priority=None, async=False):
        """Updates the firmware on all nodes.

        >>> fabric.update_firmware(package=fwpkg)

        :param package: Firmware package to update to.
        :type package: `FirmwarePackage <firmware_package.html>`_
        :param partition_arg: Which partition to update.
        :type partition_arg: string
        :param priority: SIMG header Priority setting.
        :type priority: integer
        :param async: Flag that determines if the command result (dictionary)
                      is returned or a Command object (can get status, etc.).
        :type async: boolean
        """
        self._run_command(async, "update_firmware", package,
                          partition_arg, priority)

    def config_reset(self, async=False):
        """Resets the configuration on all nodes to factory defaults.

        >>> fabric.config_reset()
        {0: None, 1: None, 2: None, 3: None}

        :param async: Flag that determines if the command result (dictionary)
                      is returned or a Command object (can get status, etc.).
        :type async: boolean

        """
        self._run_command(async, "config_reset")

    def set_boot_order(self, boot_args, async=False):
        """Sets the boot order on all nodes.

        >>> fabric.set_boot_order(boot_args=['pxe', 'disk'])

        :param boot_args: Boot order list.
        :type boot_args: list
        :param async: Flag that determines if the command result (dictionary)
                      is returned or a Command object (can get status, etc.).
        :type async: boolean

        """
        self._run_command(async, "set_boot_order", boot_args)

    def get_boot_order(self, async=False):
        """Gets the boot order from all nodes.

        >>> fabric.get_boot_order()
        {
         0: ['disk', 'pxe'],
         1: ['disk', 'pxe'],
         2: ['disk', 'pxe'],
         3: ['disk', 'pxe']
        }

        :param async: Flag that determines if the command result (dictionary)
                      is returned or a Command object (can get status, etc.).
        :type async: boolean

        :returns: The boot order of each node on this fabric.
        :rtype: dictionary or `Task <tasks.html>`_

        """
        return self._run_command(async, "get_boot_order")

    # TODO: should this be called get_versions?
    def info_basic(self, async=False):
        """Gets the version info from all nodes.

        >>> fabric.info_basic()
        {
         0: <pyipmi.info.InfoBasicResult object at 0x1f74150>,
         1: <pyipmi.info.InfoBasicResult object at 0x1f745d0>,
         2: <pyipmi.info.InfoBasicResult object at 0x1f743d0>,
         3: <pyipmi.info.InfoBasicResult object at 0x1f74650>
        }

        .. seealso::
            `Info Basic <node.html#cxmanage_api.node.Node.info_basic>`_

        :param async: Flag that determines if the command result (dictionary)
                      is returned or a Command object (can get status, etc.).
        :type async: boolean

        :returns: The basic SoC info for all nodes.
        :rtype: dictionary or `Task <tasks.html>`_

        """
        return self._run_command(async, "info_basic")

    def info_basic_dict(self, async=False):
        """Gets the version info from all nodes.

        >>> fabric.info_basic_dict()
        {0:
            {
             'a9boot_version'   : 'v2012.10.16',
             'bootlog_version'  : 'v0.9.1-39-g7e10987',
             'build_number'     : '7E10987C',
             'card'             : 'EnergyCard X02',
             'cdb_version'      : 'v0.9.1-39-g7e10987',
             'dtb_version'      : 'v3.6-rc1_cx_2012.10.02',
             'header'           : 'Calxeda SoC (0x0096CD)',
             'soc_version'      : 'v0.9.1',
             'stage2_version'   : 'v0.9.1',
             'timestamp'        : '1352911670',
             'uboot_version'    : 'v2012.07_cx_2012.10.29',
             'ubootenv_version' : 'v2012.07_cx_2012.10.29',
             'version'          : 'ECX-1000-v1.7.1'
            },
         #
         # Output trimmed for brevity ... Each remaining Nodes info_basic
         # dictionary would be printed.
         #
        }

        .. seealso::
            `Info Basic Dict <node.html#cxmanage_api.node.Node.info_basic_dict>`_

        :param async: Flag that determines if the command result (dictionary)
                      is returned or a Task object (can get status, etc.).
        :type async: boolean

        :returns: The basic SoC info for all nodes.
        :rtype: dictionary or `Task <tasks.html>`_

        """
        results = {}
        for node_number, info in self.info_basic(async=async).items():
            results[node_number] = vars(info)
        return results

    def ipmitool_command(self, ipmitool_args, asynchronous=False):
        """Run an arbitrary IPMItool command on all nodes.

        >>> # Gets eth0's MAC Address for each node ...
        >>> fabric.ipmitool_command(['cxoem', 'fabric', 'get', 'macaddr',
        >>> ...'interface', '0'])
        {
         0: 'fc:2f:40:3b:ec:40',
         1: 'fc:2f:40:91:dc:40',
         2: 'fc:2f:40:ab:f7:14',
         3: 'fc:2f:40:88:b3:6c'
        }

        :param ipmitool_args: Arguments to pass on to the ipmitool command.
        :type ipmitool_args: list
        :param async: Flag that determines if the command result (dictionary)
                      is returned or a Task object (can get status, etc.).
        :type async: boolean

        :returns: IPMI command response.
        :rtype: string

        """
        return self._run_command(asynchronous, "ipmitool_command",
                                 ipmitool_args)

    def info_dump(self, async=False):
        """Dumps info from all nodes.

        >>> fabric.info_dump()
        >>> {0: n0dump, 1: n1dump, 2: n2dump, 3: n3dump}
        >>> #
        >>> # Output condensed for brevity ...
        >>> #

        .. seealso::
            `Info Dump <node.html#cxmanage_api.node.Node.info_dump>`_

        :param async: Flag that determines if the command result (dictionary)
                      is returned or a Task object (can get status, etc.).
        :type async: boolean

        :returns: Info dump for each node. (quite large)
        :rtype: dictionary or Task object

        """
        return self._run_command(async, "info_dump")

    def get_ubootenv(self, async=False):
        """Gets the u-boot environment from all nodes.

        >>> fabric.get_ubootenv()
        {
         0: <cxmanage_api.ubootenv.UbootEnv instance at 0x7fc2d4058098>,
         1: <cxmanage_api.ubootenv.UbootEnv instance at 0x7fc2d4058908>,
         2: <cxmanage_api.ubootenv.UbootEnv instance at 0x7fc2d40582d8>,
         3: <cxmanage_api.ubootenv.UbootEnv instance at 0x7fc2d40589e0>
        }

        :param async: Flag that determines if the command result (dictionary)
                      is returned or a Task object (can get status, etc.).
        :type async: boolean

        :returns: UBootEnvironment objects for all nodes.
        :rtype: dictionary or `Task <command.html>`_

        """
        return self._run_command(async, "get_ubootenv")

    def _discover_nodes(self, ip_address, username="admin", password="admin"):
        """Gets the nodes of this fabric by pulling IP info from a BMC."""
        node = self.node(ip_address=ip_address, username=username,
                         password=password, tftp=self.tftp,
                         verbose=self.verbose)
        ipinfo = node.get_fabric_ipinfo()
        for node_id, node_address in ipinfo.iteritems():
            self._nodes[node_id] = self.node(ip_address=node_address,
                                            username=username,
                                            password=password,
                                            tftp=self.tftp,
                                            verbose=self.verbose)

    def _run_command(self, async, name, *args):
        """Start a command on the given nodes."""
        tasks = {}
        for node_id, node in self.nodes.iteritems():
            tasks[node_id] = self.task_queue.put(getattr(node, name), *args)

        if async:
            return tasks
        else:
            results = {}
            errors = {}
            for node_id, task in tasks.iteritems():
                task.join()
                if task.status == "Completed":
                    results[node_id] = task.result
                else:
                    errors[node_id] = task.errors
            if errors:
                raise CommandFailedError(results, errors)
            return results


# End of file: ./fabric.py

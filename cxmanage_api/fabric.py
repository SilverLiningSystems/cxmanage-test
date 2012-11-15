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

from cxmanage_api.command import Command
from cxmanage_api.tftp import InternalTftp
from cxmanage_api.node import Node as NODE


class Fabric(object):
    """ The Fabric class provides management of multiple nodes.
    Fabrics have the ability to send commands to:
        -> Any particular node.
        -> All nodes.

    To create a Fabric object, only a single node (ideally node 0) is needed.
    The rest of the fabric can optionally be derived via node 0.

    Note:
        * Constructing Fabric objects without a valid node 0 will mean that all
          Fabric Management commands will NOT work.
    """

    def __init__(self, ip_address, username="admin", password="admin",
            tftp=None, max_threads=1, command_delay=0, verbose=False,
            node=NODE):
        """Default constructor for the Fabric class.

        @param max_threads: Maximum number of threads to run at a time.
        @type max_threads: integer
        """
        if not tftp:
            tftp = InternalTftp()

        self.nodes = {}
        self._tftp = tftp
        self.max_threads = max_threads
        self.command_delay = command_delay
        self.verbose = verbose
        self.node = node

        self._discover_nodes(ip_address=ip_address, username=username,
                             password=password)

    def __eq__(self, other):
        return isinstance(other, Fabric) and self.nodes == other.nodes

    def __hash__(self):
        return hash(tuple(self.nodes.iteritems()))

    @property
    def tftp(self):
        """ Get the tftp server """
        return self._tftp

    @tftp.setter
    def tftp(self, value):
        """ Set the tftp server in all the nodes """
        self._tftp = value
        for node in self.nodes.values():
            node.tftp = value

############################## Public methods #################################

    def get_mac_addresses(self, asynchronous=False):
        """ Get MAC addresses from all nodes """
        return self._run_command(asynchronous, "get_mac_addresses")

    def get_power(self, asynchronous=False):
        """ Get the power status of all nodes """
        return self._run_command(asynchronous, "get_power")

    def set_power(self, mode, asynchronous=False):
        """ Set the power on all nodes """
        return self._run_command(asynchronous, "set_power", mode)

    def get_power_policy(self, asynchronous=False):
        """ Get the power policy from all nodes """
        return self._run_command(asynchronous, "get_power_policy")

    def set_power_policy(self, state, asynchronous=False):
        """ Set the power policy on all nodes """
        return self._run_command(asynchronous, "set_power_policy", state)

    def mc_reset(self, asynchronous=False):
        """ Reset the management controller on all nodes """
        return self._run_command(asynchronous, "mc_reset")

    def get_sensors(self, name="", asynchronous=False):
        """ Get sensors from all nodes """
        return self._run_command(asynchronous, "get_sensors", name)

    def get_firmware_info(self, asynchronous=False):
        """ Get firmware info from all nodes """
        return self._run_command(asynchronous, "get_firmware_info")

    def is_updatable(self, package, partition_arg="INACTIVE", priority=None,
            asynchronous=False):
        """ Check the firmware on all nodes """
        return self._run_command(asynchronous, "is_updatable", package,
                partition_arg, priority)

    def update_firmware(self, package, partition_arg="INACTIVE", priority=None,
            asynchronous=False):
        """ Update the firmware on all nodes """
        return self._run_command(asynchronous, "update_firmware", package,
                partition_arg, priority)

    def config_reset(self, asynchronous=False):
        """ Reset the configuration on all nodes """
        return self._run_command(asynchronous, "config_reset")

    def set_boot_order(self, boot_args, asynchronous=False):
        """ Set the boot order on all nodes """
        return self._run_command(asynchronous, "set_boot_order", boot_args)

    def get_boot_order(self, asynchronous=False):
        """ Get the boot order from all nodes """
        return self._run_command(asynchronous, "get_boot_order")

    # TODO: should this be called get_versions?
    def info_basic(self, asynchronous=False):
        """ Get version info from all nodes """
        return self._run_command(asynchronous, "info_basic")

    def info_dump(self, asynchronous=False):
        """ Dump info from all nodes """
        return self._run_command(asynchronous, "info_dump")

    def get_ubootenv(self, asynchronous=False):
        """ Get the u-boot environment from all nodes """
        return self._run_command(asynchronous, "get_ubootenv")

    def ipmitool_command(self, ipmitool_args, asynchronous=False):
        """ Run an arbitrary IPMItool command on all nodes """
        return self._run_command(asynchronous, "ipmitool_command",
                ipmitool_args)

############################### Private methods ###############################

    def _discover_nodes(self, ip_address, username="admin", password="admin"):
        """ Set the nodes of this fabric by pulling IP info from a BMC """
        node = self.node(ip_address=ip_address, username=username,
                         password=password, tftp=self.tftp,
                         verbose=self.verbose)

        ipinfo = node.get_fabric_ipinfo()
        for node_id, node_address in ipinfo.iteritems():
            self.nodes[node_id] = self.node(ip_address=node_address,
                                            username=username,
                                            password=password,
                                            tftp=self.tftp,
                                            verbose=self.verbose)

    def _run_command(self, asynchronous, name, *args):
        """ Start a command on the given targets """
        command = Command(self.nodes, name, args, self.command_delay,
                self.max_threads)
        command.start()
        if asynchronous:
            return command
        else:
            command.join()
            return command.get_results()

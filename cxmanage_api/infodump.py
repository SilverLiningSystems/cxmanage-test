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
"""IPMI based commands for getting various 'info' from an IPMI target."""


from pkg_resources import resource_string


def get_info_dump(node):
    """Prints the IPMI data available from the SoC.

    :param tftp: Tftp server to facilitate command/response data.
    :type tftp: InternalTftp or ExternalTftp
    :param node: Node to get info dump from.
    :type node: Node

    """
    lines = [chassis(node),
             lan(node),
             controller(node),
             sdr(node),
             sensor(node),
             fru(node),
             sel(node),
             pef(node),
             user(node),
             channel(node),
             #session(node),
             firmware(node),
             fabric(node),
             get_ubootenv(node),
             get_cdb(node),
             get_registers(node)]
    return '\n\n'.join(lines)

def ipmitool(node, cmd):
    """Run an ipmitool command on a node.

    :param node: Node to run the command on.
    :type node: Node
    :param cmd: Command to run.
    :type cmd: string

    """
    ipmitool_args = cmd.split()
    try:
        return node.ipmitool_command(ipmitool_args)

    except Exception as e:
        return "%s: %s" % (e.__class__.__name__, e)

def chassis(node):
    """Print Chassis information.

    :param tftp: Tftp server to facilitate command/response data.
    :type tftp: InternalTftp or ExternalTftp
    :param node: Node to get info dump from.
    :type node: Node

    """
    lines = ['[ IPMI Chassis status ]',
             ipmitool(node, 'chassis status') + '\n',
             '[ IPMI Chassis Power status ]',
             ipmitool(node, 'chassis power status') + '\n',
             #'[ IPMI Chassis Restart Cause ]',
             #ipmitool(node, 'chassis restart-cause'),
             '[ CXOEM Info ]',
             ipmitool(node, 'cxoem info basic') + '\n',
             ipmitool(node, 'cxoem info partnum') + '\n',
             ipmitool(node, 'cxoem info chassis') + '\n',
             ipmitool(node, 'cxoem info node') + '\n',
             '[ IPMI Chassis Boot parameters ]',
             ipmitool(node, 'chassis bootparam get 0') + '\n',
             ipmitool(node, 'chassis bootparam get 1') + '\n',
             ipmitool(node, 'chassis bootparam get 2') + '\n',
             ipmitool(node, 'chassis bootparam get 3') + '\n',
             ipmitool(node, 'chassis bootparam get 4') + '\n',
             ipmitool(node, 'chassis bootparam get 5') + '\n',
             ipmitool(node, 'chassis bootparam get 6') + '\n',
             ipmitool(node, 'chassis bootparam get 7')]
    return '\n'.join(lines)

def lan(node):
    """Print LAN information for a node.

    :param tftp: Tftp server to facilitate command/response data.
    :type tftp: InternalTftp or ExternalTftp
    :param node: Node to get info dump from.
    :type node: Node

    """
    lines = ['[ IPMI LAN Configuration ]',
             ipmitool(node, 'lan print') + '\n',
             '[ IPMI LAN Alerts ]',
             ipmitool(node, 'lan alert print') + '\n',
             '[ IPMI LAN Stats ]',
             ipmitool(node, 'lan stats get')]
    return '\n'.join(lines)

def controller(node):
    """Print management controller information.

    :param tftp: Tftp server to facilitate command/response data.
    :type tftp: InternalTftp or ExternalTftp
    :param node: Node to get info dump from.
    :type node: Node

    """
    lines = ['[ IPMI BMC GUID ]',
             ipmitool(node, 'mc guid') + '\n',
             #'[ IPMI BMC Watchdog Timer ]',
             #ipmitool(node, 'mc watchdog get') + '\n',
             '[ IPMI BMC Global Enables ]',
             ipmitool(node, 'mc getenables')]
    return '\n'.join(lines)

def sdr(node):
    """Print sensor data record information.

    :param tftp: Tftp server to facilitate command/response data.
    :type tftp: InternalTftp or ExternalTftp
    :param node: Node to get info dump from.
    :type node: Node

    """
    lines = ['[ IPMI Sensor Description Records ]',
             ipmitool(node, 'sdr')]
    return '\n'.join(lines)

def sensor(node):
    """Print sensor information.

    :param tftp: Tftp server to facilitate command/response data.
    :type tftp: InternalTftp or ExternalTftp
    :param node: Node to get info dump from.
    :type node: Node

    """
    lines = ['[ IPMI Sensors ]',
             ipmitool(node, 'sensor')]
    return '\n'.join(lines)

def fru(node):
    """Print FRU information.

    :param tftp: Tftp server to facilitate command/response data.
    :type tftp: InternalTftp or ExternalTftp
    :param node: Node to get info dump from.
    :type node: Node

    """
    lines = ['[ IPMI FRU data records ]',
             ipmitool(node, 'fru')]
    return '\n'.join(lines)

def sel(node):
    """Print the event log.

    :param tftp: Tftp server to facilitate command/response data.
    :type tftp: InternalTftp or ExternalTftp
    :param node: Node to get info dump from.
    :type node: Node

    """
    lines = ['[ IPMI System Event Log ]',
             ipmitool(node, 'sel')]
    return '\n'.join(lines)

def pef(node):
    """Print PEF information.

    :param tftp: Tftp server to facilitate command/response data.
    :type tftp: InternalTftp or ExternalTftp
    :param node: Node to get info dump from.
    :type node: Node

    """
    lines = ['[ IPMI Platform Event Filters ]',
             ipmitool(node, 'pef')]
    return '\n'.join(lines)

def user(node):
    """Print user information.

    :param tftp: Tftp server to facilitate command/response data.
    :type tftp: InternalTftp or ExternalTftp
    :param node: Node to get info dump from.
    :type node: Node

    """
    lines = ['[ IPMI Users ]',
             ipmitool(node, 'user list')]
    return '\n'.join(lines)

def session(node):
    """Print session information.

    :param tftp: Tftp server to facilitate command/response data.
    :type tftp: InternalTftp or ExternalTftp
    :param node: Node to get info dump from.
    :type node: Node

    """
    lines = [
             # FIXME: This command seems to cause an mpu fault
             #'[ IPMI Sessions Info ]',
             #ipmitool(node, 'session info all')
            ]
    return '\n'.join(lines)

def channel(node):
    """Print channel information.

    :param tftp: Tftp server to facilitate command/response data.
    :type tftp: InternalTftp or ExternalTftp
    :param node: Node to get info dump from.
    :type node: Node

    """
    lines = [#'[ IPMI Channel Access ]',
             #ipmitool(node, 'channel getaccess'),
             '[ IPMI Channel Info ]',
             ipmitool(node, 'channel info')
             #'[ IPMI Channel Ciphers ]',
             #ipmitool(node, 'channel getciphers')
            ]
    return '\n'.join(lines)

def firmware(node):
    """ Print firmware information.

    :param tftp: Tftp server to facilitate command/response data.
    :type tftp: InternalTftp or ExternalTftp
    :param node: Node to get info dump from.
    :type node: Node

    """
    lines = ['[ IPMI Firmware Info ]',
             ipmitool(node, 'cxoem fw info')]
    return '\n'.join(lines)

def fabric(node):
    """Print the fabric-related data.

    :param tftp: Tftp server to facilitate command/response data.
    :type tftp: InternalTftp or ExternalTftp
    :param node: Node to get info dump from.
    :type node: Node

    """
    lines = ['[ CXOEM Fabric Data ]']
    ipinfo = {}
    try:
        ipinfo = node.get_fabric_ipinfo()
        for x in ipinfo.iteritems():
            lines.append('Node %i: %s' % x)
    except Exception as e:
        lines.append('%s: %s' % (e.__class__.__name__, e))

    try:
        macaddrs = node.get_mac_addresses()
        for i in xrange(len(macaddrs)):
            lines.append('Port %i: %s' % (i, macaddrs[i]))
    except Exception as e:
        lines.append('%s: %s' % (e.__class__.__name__, e))

    for node_id, node_address in ipinfo.iteritems():
        for item in ['netmask', 'defgw', 'ipsrc']:
            value = ipmitool(node, 'cxoem fabric get %s node %i'
                    % (item, node_id))
            lines.append('Node %i, %s: %s' % (node_id, item, value))
    return '\n'.join(lines)

def get_ubootenv(node):
    """ Print u-boot environment variables.

    :param tftp: Tftp server to facilitate command/response data.
    :type tftp: InternalTftp or ExternalTftp
    :param node: Node to get info dump from.
    :type node: Node

    """
    lines = ['[ U-Boot Environment ]']
    try:
        ubootenv = node.get_ubootenv()

        for variable in sorted(ubootenv.variables):
            lines.append('%s=%s' % (variable, ubootenv.variables[variable]))

    except Exception as e:
        lines.append('%s: %s' % (e.__class__.__name__, e))

    return '\n'.join(lines)

def get_cdb(node, cids=None):
    """Print info for each CDB entry.

    :param node: Node to get info dump from.
    :type node: Node
    :param cids: List of cids.
    :type cids: list

    """
    lines = []

    if (cids == None):
        string = resource_string('cxmanage_api', 'data/cids')
        cids = set()
        for line in string.splitlines():
            for entry in line.partition('#')[0].split():
                cids.add(entry)
        cids = sorted(cids)

    for cid in cids:
        lines.append('[ CDB %s ]' % cid)
        output = ipmitool(node, 'cxoem data cdb read 64 %s' % cid)
        size_lines = [x for x in output.split('\n')
                      if x.startswith('CID size')]
        value_lines = [x for x in output.split('\n') if x.startswith('Value')]

        if ((len(size_lines) == 1) and (len(value_lines) == 1)):
            lines.append('CID size : %s' %
                    size_lines[0].partition(':')[2].strip())
            lines.append('Value    : %s' %
                    value_lines[0].partition(':')[2].strip())
        else:
            lines.append(output)
        lines.append('')
    return '\n'.join(lines).rstrip()


def get_registers(node, regfile=None):
    """Print info for each register.

    :param node: Node to get info dump from.
    :type node: Node
    :param regfile: Register file to read from. (path)
    :type regfile: string

    """
    lines = ['[ Memory dump ]']
    register_ranges = get_register_ranges(regfile)
    for register_range in register_ranges:
        address = register_range[0]
        while (address <= register_range[1]):
            # Calculate the number of words/bytes to read
            words_remaining = (register_range[1] - address) / 4 + 1
            words_to_read = min(8, words_remaining)
            bytes_to_read = words_to_read * 4

            # Get the output
            output = ipmitool(node, 'cxoem data mem read %i %08x'
                    % (bytes_to_read, address))

            try:
                # Parse values
                values = [x for x in output.split('\n') if
                          x.startswith('Value')][0]
                values = values.partition(':')[2].strip()
                values = values.split('0x')[1:]
                values = ['0x' + x for x in values]

                # Print
                for i in range(words_to_read):
                    lines.append('Memory address %08x: %s' % (address + i * 4,
                            values[i]))

            except Exception:
                lines.append('Failed to read memory address %08x' % address)
                return '\n'.join(lines)

            address += bytes_to_read

    return '\n'.join(lines)

def get_register_ranges(regfile=None):
    """Get registers as a list of (start, end) ranges

    :param regfile: Register file to read. (path)
    :type regfile: string

    """
    if (regfile == None):
        string = resource_string('cxmanage_api', 'data/registers')
    else:
        string = open(regfile).read()

    registers = set()
    for line in string.splitlines():
        for entry in line.partition('#')[0].split():
            registers.add(int(entry, 16))
    registers = sorted(registers)

    # Build register ranges
    register_ranges = []
    start = 0
    while start < len(registers):
        end = start
        while (end + 1 < len(registers) and
                registers[end + 1] == registers[end] + 4):
            end += 1
        register_ranges.append((registers[start], registers[end]))
        start = end + 1

    return register_ranges


# End of file: ./infodump.py

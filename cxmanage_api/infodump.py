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


from pkg_resources import resource_string


def get_info_dump(node):
    """Prints the IPMI data available from the SoC.

    >>> from cxmanage_api.node import Node
    >>> from cxmanage_api.infodump import get_info_dump
    >>> n = Node('10.20.1.9')
    >>> get_info_dump(node=n)
    '[ IPMI Chassis status ]\\nSystem Power         ...'
    >>> #
    >>> # Output trimmed for brevity ... info_dump creates a string ~120k chars long.
    >>> #

    :param node: Node to get info dump from.
    :type node: Node

    :returns: IPMI data from the SoC.
    :rtype: string

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
             # session(node),
             firmware(node),
             fabric(node),
             get_ubootenv(node),
             get_cdb(node),
             get_registers(node)]
    return '\n\n'.join(lines)

def ipmitool(node, cmd):
    """Runs an ipmitool command on a node.

    >>> from cxmanage_api.node import Node
    >>> n = Node('10.20.1.9')
    >>> from cxmanage_api.infodump import ipmitool
    >>> ipmitool(node=n, cmd='cxoem info basic')
    'Calxeda SoC (0x0096CD)\\n
     Firmware Version: ECX-1000-v1.7.1-dirty\\n
     SoC Version: 0.9.1\\n
     Build Number: 7E10987C \\n
     Timestamp (1352911670): Wed Nov 14 10:47:50 2012'

    :param node: Node to run the command on.
    :type node: Node
    :param cmd: Command to run.
    :type cmd: string

    :returns: IPMI command response.
    :rtype: string

    .. seealso::
        Node `ipmitool_command <node.html#cxmanage_api.node.Node.ipmitool_command>`_

    """
    ipmitool_args = cmd.split()
    try:
        return node.ipmitool_command(ipmitool_args)
    except Exception as e:
        return "%s: %s" % (e.__class__.__name__, e)

def chassis(node):
    """Prints Chassis information.

    >>> from cxmanage_api.node import Node
    >>> n = Node('10.20.1.9')
    >>> from cxmanage_api.infodump import chassis
    >>> chassis(node=n)
    "[ IPMI Chassis status ] ..."
    >>> #
    >>> # Output trimed for brevity ... creates a string ~2.5k chars long.
    >>> #

    :param node: Node to get info dump from.
    :type node: Node

    :returns: Chasis information.
    :rtype: string

    """
    lines = ['[ IPMI Chassis status ]',
             ipmitool(node, 'chassis status') + '\n',
             '[ IPMI Chassis Power status ]',
             ipmitool(node, 'chassis power status') + '\n',
             # '[ IPMI Chassis Restart Cause ]',
             # ipmitool(node, 'chassis restart-cause'),
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
    """Prints LAN information for a node.

    >>> from cxmanage_api.node import Node
    >>> n = Node('10.20.1.9')
    >>> lan(node=n)
    '[ IPMI LAN Configuration ] ... '
    >>> #
    >>> # Output trimmed for brevity ... lan produces a string ~6k chars long.
    >>> #

    :param node: Node to get info dump from.
    :type node: Node

    :returns: LAN information.
    :rtype: string

    """
    lines = ['[ IPMI LAN Configuration ]',
             ipmitool(node, 'lan print') + '\n',
             '[ IPMI LAN Alerts ]',
             ipmitool(node, 'lan alert print') + '\n',
             '[ IPMI LAN Stats ]',
             ipmitool(node, 'lan stats get')]
    return '\n'.join(lines)

def controller(node):
    """Prints management controller information.

    >>> from cxmanage_api.node import Node
    >>> n = Node('10.20.1.9')
    >>> from cxmanage_api.infodump import controller
    >>> controller(node=n)
    '[ IPMI BMC GUID ]\\n
     System GUID  : 9026e400-c075-11e1-409f-2aa3aeedbd4e\\n
     Timestamp    : 08/21/2046 07:37:20\\n\\n
     [ IPMI BMC Global Enables ]\\n
     Receive Message Queue Interrupt          : disabled\\n
     Event Message Buffer Full Interrupt      : disabled\\n
     Event Message Buffer                     : disabled\\n
     System Event Logging                     : enabled\\n
     OEM 0                                    : disabled\\n
     OEM 1                                    : disabled\\n
     OEM 2                                    : disabled'


    :param node: Node to get info dump from.
    :type node: Node

    :returns: Management controller information.
    :rtype: string

    """
    lines = ['[ IPMI BMC GUID ]',
             ipmitool(node, 'mc guid') + '\n',
             # '[ IPMI BMC Watchdog Timer ]',
             # ipmitool(node, 'mc watchdog get') + '\n',
             '[ IPMI BMC Global Enables ]',
             ipmitool(node, 'mc getenables')]
    return '\n'.join(lines)

def sdr(node):
    """Prints sensor data record information.

    >>> from cxmanage_api.node import Node
    >>> n = Node('10.20.1.9')
    >>> from cxmanage_api.infodump import controller
    >>> controller(node=n)
    '[ IPMI BMC GUID ] ...'
    >>> #
    >>> # Output trimmed for brevity ... sdr creates a string ~1k chars long.
    >>> #

    :param node: Node to get info dump from.
    :type node: Node

    :return: Sensor data record information.
    :rtype: string

    """
    lines = ['[ IPMI Sensor Description Records ]',
             ipmitool(node, 'sdr')]
    return '\n'.join(lines)

def sensor(node):
    """Prints sensor information.

    >>> from cxmanage_api.node import Node
    >>> n = Node('10.20.1.9')
    >>> from cxmanage_api.infodump import sensor
    >>> sensor(node=n)
    '[ IPMI Sensors ] ...'
    >>> #
    >>> # Output trimmed for brevity ... sensor creates a string ~4k chars long.
    >>> #

    :param node: Node to get info dump from.
    :type node: Node

    :returns: Sensor information.
    :rtype: string

    """
    lines = ['[ IPMI Sensors ]',
             ipmitool(node, 'sensor')]
    return '\n'.join(lines)

def fru(node):
    """Print FRU information.

    >>> from cxmanage_api.node import Node
    >>> n = Node('10.20.1.9')

    :param node: Node to get info dump from.
    :type node: Node

    """
    lines = ['[ IPMI FRU data records ]',
             ipmitool(node, 'fru')]
    return '\n'.join(lines)

def sel(node):
    """Print the system event log.

    >>> from cxmanage_api.node import Node
    >>> n = Node('10.20.1.9')
    >>> from cxmanage_api.infodump import sel
    >>> sel(node=n)
    "[ IPMI System Event Log ]\\n
     SEL Information\\n
     Version          : 1.5 (v1.5, v2 compliant)\\n
     Entries          : 25\\n
     Free Space       : 65120 bytes \\n
     Percent Used     : 0%\\n
     Last Add Time    : 11/15/2012 17:20:41\\n
     Last Del Time    : Not Available\\n
     Overflow         : false\\n
     Supported Cmds   : 'Reserve' 'Get Alloc Info' \\n
     # of Alloc Units : 4095\\n
     Alloc Unit Size  : 16\\n
     # Free Units     : 4070\\n
     Largest Free Blk : 4070\\n
     Max Record Size  : 1"

    :param node: Node to get info dump from.
    :type node: Node

    :returns: System event log information.
    :rtype: string

    """
    lines = ['[ IPMI System Event Log ]',
             ipmitool(node, 'sel')]
    return '\n'.join(lines)

def pef(node):
    """Prints PEF information.

    >>> from cxmanage_api.node import Node
    >>> n = Node('10.20.1.9')
    >>> from cxmanage_api.infodump import pef
    >>> pef(node=n)
    '[ IPMI Platform Event Filters ]\\n
    0x51 | 32 | 20 | 00e42690-75c0-e111-409f-2aa3aeedbd4e | Alert,Power-off,Reset,Power-cycle'

    :param node: Node to get info dump from.
    :type node: Node

    :returns: PEF information.
    :rtype: string

    """
    lines = ['[ IPMI Platform Event Filters ]',
             ipmitool(node, 'pef')]
    return '\n'.join(lines)

def user(node):
    """Prints user information.

    >>> from cxmanage_api.node import Node
    >>> n = Node('10.20.1.9')
    >>> from cxmanage_api.infodump import user
    >>> user(node=n)
    '[ IPMI Users ]\\n
    ID  Name     Callin  Link Auth IPMI Msg   Channel Priv Limit\\n
    2   admin    true    false     false      ADMINISTRATOR'

    :param node: Node to get info dump from.
    :type node: Node

    :returns: User information.
    :rtype: string

    """
    lines = ['[ IPMI Users ]',
             ipmitool(node, 'user list')]
    return '\n'.join(lines)

def session(node):
    """Prints session information.

    >>> from cxmanage_api.node import Node
    >>> n = Node('10.20.1.9')
    >>> from cxmanage_api.infodump import session
    >>> session(node=n)
    ''

    :param node: Node to get info dump from.
    :type node: Node

    :returns: Session information.
    :rtype: string

    """
    lines = [
             # FIXME: This command seems to cause an mpu fault
             # '[ IPMI Sessions Info ]',
             # ipmitool(node, 'session info all')
            ]
    return '\n'.join(lines)

def channel(node):
    """Prints channel information.

    >>> from cxmanage_api.node import Node
    >>> n = Node('10.20.1.9')
    >>> from cxmanage_api.infodump import channel
    >>> channel(node=n)
    '[ IPMI Channel Info ]\\n
     Channel 0x1 info:\\n
     Channel Medium Type   : 802.3 LAN\\n
     Channel Protocol Type : IPMB-1.0\\n
     Session Support       : multi-session\\n
     Active Session Count  : 1\\n
     Protocol Vendor ID    : 7154\\n
     Volatile(active) Settings\\n
     Alerting            : enabled\\n
     Per-message Auth    : enabled\\n
     User Level Auth     : enabled\\n
     Access Mode         : disabled\\n
     Non-Volatile Settings\\n
     Alerting            : enabled\\n
     Per-message Auth    : enabled\\n
     User Level Auth     : enabled\\n
     Access Mode         : disabled'

    :param node: Node to get info dump from.
    :type node: Node

    :returns: Channel information.
    :rtype: string

    """
    lines = [  # '[ IPMI Channel Access ]',
             # ipmitool(node, 'channel getaccess'),
             '[ IPMI Channel Info ]',
             ipmitool(node, 'channel info')
             # '[ IPMI Channel Ciphers ]',
             # ipmitool(node, 'channel getciphers')
            ]
    return '\n'.join(lines)

def firmware(node):
    """Prints firmware information.

    >>> from cxmanage_api.node import Node
    >>> n = Node('10.20.1.9')
    >>> from cxmanage_api.infodump import firmware
    >>> firmware(node=n)
    '[ IPMI Firmware Info ]\\n
    Partition          : 00\\n
    Type               : 02 (S2_ELF)\\n
    Offset             : 00000000\\n
    Size               : 00005000\\n
    Priority           : 00000004\\n
    Daddr              : 20029000\\n
    Flags              : fffffffd\\n
    Version            : v0.9.1-39-g7e10987\\n
    In Use             : Unknown\\n
    ...'
    >>> #
    >>> # Output trimmed for brevity ... firmware creates a string ~5k chars long.
    >>> #

    :param node: Node to get info dump from.
    :type node: Node

    :returns: Firmware information.
    :rtype: string

    """
    lines = ['[ IPMI Firmware Info ]',
             ipmitool(node, 'cxoem fw info')]
    return '\n'.join(lines)

def fabric(node):
    """Prints the fabric-related data.

    >>> from cxmanage_api.node import Node
    >>> n = Node('10.20.1.9')
    >>> from cxmanage_api.infodump import fabric
    >>> fabric(node=n)
    '[ CXOEM Fabric Data ]\\n
    Node 0: 10.20.1.9\\n
    Node 1: 10.20.2.131\\n
    Node 2: 10.20.0.220\\n
    Node 3: 10.20.2.5\\n
    Port 0: fc:2f:40:3b:ec:40\\n
    Port 1: fc:2f:40:3b:ec:41\\n
    Port 2: fc:2f:40:3b:ec:42\\n
    Node 0, netmask: 255.255.255.0\\n
    Node 0, defgw: 192.168.100.254\\n
    Node 0, ipsrc: 2\\n
    Node 1, netmask: 0.0.0.0\\n
    Node 1, defgw: 0.0.0.0\\n
    Node 1, ipsrc: 2\\n
    Node 2, netmask: 0.0.0.0\\n
    Node 2, defgw: 0.0.0.0\\n
    Node 2, ipsrc: 2\\n
    Node 3, netmask: 0.0.0.0\\n
    Node 3, defgw: 0.0.0.0\\n
    Node 3, ipsrc: 2'

    :param node: Node to get info dump from.
    :type node: Node

    :returns fabric-related data.
    :rtype: string

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
    """ Prints u-boot environment variables.

    >>> from cxmanage_api.node import Node
    >>> n = Node('10.20.1.9')
    >>> from cxmanage_api.infodump import get_ubootenv
    >>> get_ubootenv(node=n)
    '[ U-Boot Environment ] ...'
    >>> #
    >>> # Output trimmed for brevity ... get_ubootenv creates a string ~1.5k chars long.
    >>> #

    :param node: Node to get info dump from.
    :type node: Node

    :returns: U-Boot Environment information.
    :rtype: string

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
    """Prints info for each CDB entry.

    >>> from cxmanage_api.node import Node
    >>> n = Node('10.20.1.9')
    >>> from cxmanage_api.infodump import get_cdb
    >>> get_cdb(node=n)
    '[ CDB 00000001 ] ... [ CDB 0000000N ]'
    >>> #
    >>> # Output trimmed for brevity ... get_cdb creates a string ~4.7k chars long.
    >>> #

    :param node: Node to get info dump from.
    :type node: Node
    :param cids: List of cids.
    :type cids: list

    :returns: Info for every CDB entry.
    :rtype: string

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
    """Prints info for each register.

    >>> from cxmanage_api.node import Node
    >>> n = Node('10.20.1.9')
    >>> from cxmanage_api.infodump import get_registers
    >>> get_registers(node=n)
    '[ Memory dump ] ...'
    >>> #
    >>> # Output trimmed for brevity ... get_registers creates a string ~10k chars long.
    >>> #

    :param node: Node to get info dump from.
    :type node: Node
    :param regfile: Register file to read from. (path)
    :type regfile: string

    :returns: Information for each register.
    :rtype: string

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

    >>> from cxmanage_api.infodump import get_register_ranges
    >>> get_register_ranges(regfile='my_regfile.txt')
    [xxxxxx, xxxxxxx, xxxxxx]
    >>> #
    >>> # Need real world example here ...
    >>> #

    :param regfile: Register file to read. (path)
    :type regfile: string

    :returns: A list of ranges from start to end.
    :rtype: list

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

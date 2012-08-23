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

def get_info_dump(tftp, target):
    """ Print the IPMI data available from the SoC. """
    lines = [
        chassis(tftp, target),
        lan(tftp, target),
        controller(tftp, target),
        sdr(tftp, target),
        sensor(tftp, target),
        fru(tftp, target),
        sel(tftp, target),
        pef(tftp, target),
        user(tftp, target),
        channel(tftp, target),
        #session(tftp, target),
        firmware(tftp, target),
        fabric(tftp, target),
        get_ubootenv(tftp, target),
        get_cdb(target),
        get_registers(target)
    ]
    return '\n\n'.join(lines)

def ipmitool(target, cmd):
    """ Run an ipmitool command on the target """
    ipmitool_args = cmd.split()
    try:
        return target.ipmitool_command(ipmitool_args)
    except Exception as e:
        return "%s: %s" % (e.__class__.__name__, e)

def chassis(tftp, target):
    """ Print Chassis information. """
    lines = [
        '[ IPMI Chassis status ]',
        ipmitool(target, 'chassis status') + '\n',
        '[ IPMI Chassis Power status ]',
        ipmitool(target, 'chassis power status') + '\n',
        #'[ IPMI Chassis Restart Cause ]',
        #ipmitool(target, 'chassis restart-cause'),
        '[ CXOEM Info ]',
        ipmitool(target, 'cxoem info basic') + '\n',
        ipmitool(target, 'cxoem info partnum') + '\n',
        ipmitool(target, 'cxoem info chassis') + '\n',
        ipmitool(target, 'cxoem info node') + '\n',
         '[ IPMI Chassis Boot parameters ]',
        ipmitool(target, 'chassis bootparam get 0') + '\n',
        ipmitool(target, 'chassis bootparam get 1') + '\n',
        ipmitool(target, 'chassis bootparam get 2') + '\n',
        ipmitool(target, 'chassis bootparam get 3') + '\n',
        ipmitool(target, 'chassis bootparam get 4') + '\n',
        ipmitool(target, 'chassis bootparam get 5') + '\n',
        ipmitool(target, 'chassis bootparam get 6') + '\n',
        ipmitool(target, 'chassis bootparam get 7')
    ]
    return '\n'.join(lines)

def lan(tftp, target):
    """ Print LAN information. """
    lines = [
        '[ IPMI LAN Configuration ]',
        ipmitool(target, 'lan print') + '\n',
        '[ IPMI LAN Alerts ]',
        ipmitool(target, 'lan alert print') + '\n',
        '[ IPMI LAN Stats ]',
        ipmitool(target, 'lan stats get')
    ]
    return '\n'.join(lines)

def controller(tftp, target):
    """ Print management controller information. """
    lines = [
        '[ IPMI BMC GUID ]',
        ipmitool(target, 'mc guid') + '\n',
        #'[ IPMI BMC Watchdog Timer ]',
        #ipmitool(target, 'mc watchdog get') + '\n',
        '[ IPMI BMC Global Enables ]',
        ipmitool(target, 'mc getenables')
    ]
    return '\n'.join(lines)

def sdr(tftp, target):
    """ Print sensor data record information. """
    lines = [
        '[ IPMI Sensor Description Records ]',
        ipmitool(target, 'sdr')
    ]
    return '\n'.join(lines)

def sensor(tftp, target):
    """ Print sensor information """
    lines = [
        '[ IPMI Sensors ]',
        ipmitool(target, 'sensor')
    ]
    return '\n'.join(lines)

def fru(tftp, target):
    """ Print FRU information. """
    lines = [
        '[ IPMI FRU data records ]',
        ipmitool(target, 'fru')
    ]
    return '\n'.join(lines)

def sel(tftp, target):
    """ Print event log. """
    lines = [
        '[ IPMI System Event Log ]',
        ipmitool(target, 'sel')
    ]
    return '\n'.join(lines)

def pef(tftp, target):
    """ Print PEF information. """
    lines = [
        '[ IPMI Platform Event Filters ]',
        ipmitool(target, 'pef')
    ]
    return '\n'.join(lines)

def user(tftp, target):
    """ Print user information. """
    lines = [
        '[ IPMI Users ]',
        ipmitool(target, 'user list')
    ]
    return '\n'.join(lines)

def session(tftp, target):
    """ Print session information. """
    lines = [
        # FIXME: This command seems to cause an mpu fault
        #'[ IPMI Sessions Info ]',
        #ipmitool(target, 'session info all')
    ]
    return '\n'.join(lines)

def channel(tftp, target):
    """ Print channel information. """
    lines = [
        #'[ IPMI Channel Access ]',
        #ipmitool(target, 'channel getaccess'),
        '[ IPMI Channel Info ]',
        ipmitool(target, 'channel info')
        #'[ IPMI Channel Ciphers ]',
        #ipmitool(target, 'channel getciphers')
    ]
    return '\n'.join(lines)

def firmware(tftp, target):
    """ Print firmware information. """
    lines = [
        '[ IPMI Firmware Info ]',
        ipmitool(target, 'cxoem fw info')
    ]
    return '\n'.join(lines)

def fabric(tftp, target):
    """ Print the fabric-related data. """
    lines = [
        '[ CXOEM Fabric Data ]'
    ]

    ipinfo = []
    try:
        ipinfo = target.get_ipinfo(tftp)
        for entry in ipinfo:
            lines.append('Node %i: %s' % entry)
    except Exception as e:
        lines.append('%s: %s' % (e.__class__.__name__, e))

    try:
        macaddrs = target.get_macaddrs(tftp)
        for entry in macaddrs:
            lines.append('Node %i, Port %i: %s' % entry)
    except Exception as e:
        lines.append('%s: %s' % (e.__class__.__name__, e))

    for entry in ipinfo:
        node_id = entry[0]
        for item in ['netmask', 'defgw', 'ipsrc']:
            value = ipmitool(target, 'cxoem fabric get %s node %i'
                    % (item, node_id))
            lines.append('Node %i, %s: %s' % (node_id, item, value))

    return '\n'.join(lines)


def get_ubootenv(tftp, target):
    """ Print u-boot environment variables """
    lines = [
        '[ U-Boot Environment ]'
    ]

    try:
        fwinfo = target.get_firmware_info()
        partition = target._get_partition(fwinfo, "UBOOTENV", "ACTIVE")
        ubootenv = target._download_ubootenv(tftp, partition)
        for variable in sorted(ubootenv.variables):
            lines.append('%s=%s' % (variable, ubootenv.variables[variable]))
    except Exception as e:
        lines.append('%s: %s' % (e.__class__.__name__, e))

    return '\n'.join(lines)

def get_cdb(target, cids=None):
    """ Print info for each CDB entry. """
    lines = []

    if cids == None:
        string = resource_string('cxmanage', 'data/cids')
        cids = set()
        for line in string.splitlines():
            for entry in line.partition('#')[0].split():
                cids.add(entry)
        cids = sorted(cids)

    for cid in cids:
        lines.append('[ CDB %s ]' % cid)
        output = ipmitool(target, 'cxoem data cdb read 64 %s' % cid)
        size_lines = [x for x in output.split('\n')
                if x.startswith('CID size')]
        value_lines = [x for x in output.split('\n') if x.startswith('Value')]

        if len(size_lines) == 1 and len(value_lines) == 1:
            lines.append('CID size : %s' %
                    size_lines[0].partition(':')[2].strip())
            lines.append('Value    : %s' %
                    value_lines[0].partition(':')[2].strip())
        else:
            lines.append(output)
        lines.append('')

    return '\n'.join(lines).rstrip()


def get_registers(target, regfile=None):
    """ Print info for each register. """
    lines = [
        '[ Memory dump ]'
    ]

    register_ranges = get_register_ranges(regfile)
    for register_range in register_ranges:
        address = register_range[0]
        while address <= register_range[1]:
            # Calculate the number of words/bytes to read
            words_remaining = (register_range[1] - address) / 4 + 1
            words_to_read = min(8, words_remaining)
            bytes_to_read = words_to_read * 4

            # Get the output
            output = ipmitool(target, 'cxoem data mem read %i %08x'
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
            except:
                lines.append('Failed to read memory address %08x' % address)
                return '\n'.join(lines)

            address += bytes_to_read

    return '\n'.join(lines)

def get_register_ranges(regfile=None):
    """ Get registers as a list of (start, end) ranges """
    if regfile == None:
        string = resource_string('cxmanage', 'data/registers')
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

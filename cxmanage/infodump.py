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

def print_info_dump(tftp, target):
    """ Print the IPMI data available from the SoC. """
    # See if we need a tftp server
    chassis(tftp, target)
    lan(tftp, target)
    power(tftp, target)
    event(tftp, target)
    controller(tftp, target)
    sdr(tftp, target)
    sensor(tftp, target)
    fru(tftp, target)
    sel(tftp, target)
    pef(tftp, target)
    user(tftp, target)
    channel(tftp, target)
    session(tftp, target)
    firmware(tftp, target)
    fabric(tftp, target)

    print_ubootenv(tftp, target)

    print_cdb(target)
    print_registers(target)

def ipmitool(target, cmd):
    """ Run an ipmitool command on the target """
    ipmitool_args = cmd.split()
    try:
        return target.ipmitool_command(ipmitool_args)
    except Exception as e:
        return "%s: %s" % (e.__class__.__name__, e)

def chassis(tftp, target):
    """ Print Chassis information. """
    print '[ IPMI Chassis status ]'
    print ipmitool(target, 'chassis status') + '\n'
    print '[ IPMI Chassis Power status ]'
    print ipmitool(target, 'chassis power status') + '\n'
    #print '[ IPMI Chassis Restart Cause ]'
    #print ipmitool(target, 'chassis restart-cause')
    print '[ CXOEM Info ]'
    print ipmitool(target, 'cxoem info basic') + '\n'
    print ipmitool(target, 'cxoem info partnum') + '\n'
    print ipmitool(target, 'cxoem info chassis') + '\n'
    print ipmitool(target, 'cxoem info node') + '\n'
    print '[ IPMI Chassis Boot parameters ]'
    print ipmitool(target, 'chassis bootparam get 0') + '\n'
    print ipmitool(target, 'chassis bootparam get 1') + '\n'
    print ipmitool(target, 'chassis bootparam get 2') + '\n'
    print ipmitool(target, 'chassis bootparam get 3') + '\n'
    print ipmitool(target, 'chassis bootparam get 4') + '\n'
    print ipmitool(target, 'chassis bootparam get 5') + '\n'
    print ipmitool(target, 'chassis bootparam get 6') + '\n'
    print ipmitool(target, 'chassis bootparam get 7') + '\n'

def lan(tftp, target):
    """ Print LAN information. """
    print '[ IPMI LAN Configuration ]'
    print ipmitool(target, 'lan print') + '\n'
    print '[ IPMI LAN Alerts ]'
    print ipmitool(target, 'lan alert print') + '\n'
    print '[ IPMI LAN Stats ]'
    print ipmitool(target, 'lan stats get') + '\n'

def power(tftp, target):
    """ If there were power commands that it makes sense to issue, they would
    be here. """
    pass

def event(tftp, target):
    """ If there were event commands that it makes sense to issue, they would
    be here. """
    pass

def controller(tftp, target):
    """ Print management controller information. """
    print '[ IPMI BMC GUID ]'
    print ipmitool(target, 'mc guid') + '\n'
    #print '[ IPMI BMC Watchdog Timer ]'
    #print ipmitool(target, 'mc watchdog get') + '\n'
    print '[ IPMI BMC Global Enables ]'
    print ipmitool(target, 'mc getenables') + '\n'

def sdr(tftp, target):
    """ Print sensor data record information. """
    print '[ IPMI Sensor Description Records ]'
    print ipmitool(target, 'sdr') + '\n'

def sensor(tftp, target):
    """ Print sensor information """
    print '[ IPMI Sensors ]'
    print ipmitool(target, 'sensor') + '\n'

def fru(tftp, target):
    """ Print FRU information. """
    print '[ IPMI FRU data records ]'
    print ipmitool(target, 'fru') + '\n'

def sel(tftp, target):
    """ Print event log. """
    print '[ IPMI System Event Log ]'
    print ipmitool(target, 'sel') + '\n'

def pef(tftp, target):
    """ Print PEF information. """
    print '[ IPMI Platform Event Filters ]'
    print ipmitool(target, 'pef') + '\n'

def user(tftp, target):
    """ Print user information. """
    print '[ IPMI Users ]'
    print ipmitool(target, 'user list') + '\n'

def session(tftp, target):
    """ Print session information. """
    # FIXME: This command seems to cause an mpu fault, so disable it for now.
    # print '[ IPMI Sessions Info ]'
    # print ipmitool(target, 'session info all') + '\n'

def channel(tftp, target):
    """ Print channel information. """
    #print '[ IPMI Channel Access ]'
    #print ipmitool(target, 'channel getaccess')
    print '[ IPMI Channel Info ]'
    print ipmitool(target, 'channel info') + '\n'
    #print '[ IPMI Channel Ciphers ]'
    #print ipmitool(target, 'channel getciphers')

def firmware(tftp, target):
    """ Print firmware information. """
    print '[ IPMI Firmware Info ]'
    print ipmitool(target, 'cxoem fw info') + '\n'

def fabric(tftp, target):
    """ Print the fabric-related data. """
    print '[ CXOEM Fabric Data ]'

    ipinfo = []
    try:
        ipinfo = target.get_ipinfo(tftp)
        for entry in ipinfo:
            print 'Node %i: %s' % entry
    except Exception as e:
        print '%s: %s' % (e.__class__.__name__, e)

    try:
        macaddrs = target.get_macaddrs(tftp)
        for entry in macaddrs:
            print 'Node %i, Port %i: %s' % entry
    except Exception as e:
        print '%s: %s' % (e.__class__.__name__, e)

    for entry in ipinfo:
        node_id = entry[0]
        for item in ['netmask', 'defgw', 'ipsrc']:
            value = ipmitool(target, 'cxoem fabric get %s node %i'
                    % (item, node_id))
            print 'Node %i, %s: %s' % (node_id, item, value)
    print


def print_ubootenv(tftp, target):
    """ Print u-boot environment variables """
    print '[ U-Boot Environment ]'
    try:
        fwinfo = target.get_firmware_info()
        slot = target._get_slot(fwinfo, "UBOOTENV", "ACTIVE")
        ubootenv = target._download_ubootenv(tftp, slot)
        for variable in sorted(ubootenv.variables):
            print '%s=%s' % (variable, ubootenv.variables[variable])
    except Exception as e:
        print '%s: %s' % (e.__class__.__name__, e)
    print

def print_cdb(target, cids=None):
    """ Print info for each CDB entry. """
    if cids == None:
        cids = resource_string('cxmanage', 'data/cids').split()

    for cid in cids:
        print '[ CDB %s ]' % cid
        output = ipmitool(target, 'cxoem data cdb read 64 %s' % cid)
        size_lines = [x for x in output.split('\n')
                if x.startswith('CID size')]
        value_lines = [x for x in output.split('\n') if x.startswith('Value')]

        if len(size_lines) == 1 and len(value_lines) == 1:
            print 'CID size : %s' % size_lines[0].partition(':')[2].strip()
            print 'Value    : %s' % value_lines[0].partition(':')[2].strip()
        else:
            print output
        print


def print_registers(target, regfile=None):
    """ Print info for each register. """
    register_ranges = get_register_ranges(regfile)

    print '[ Memory dump ]'
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
                    print 'Memory address %08x: %s' % (address + i * 4,
                            values[i])
            except:
                print 'Failed to read memory address %08x' % address
                return

            address += bytes_to_read

def get_register_ranges(regfile=None):
    """ Get registers as a list of (start, end) ranges """
    if regfile == None:
        string = resource_string('cxmanage', 'data/registers')
    else:
        string = open(regfile).read()

    registers = sorted(set(int(x, 16) for x in string.split()))

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

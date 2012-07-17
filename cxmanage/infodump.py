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

import sys

from pkg_resources import resource_string

def print_info_dump(work_dir, tftp, target):
    """ Print the IPMI data available from the SoC. """
    # See if we need a tftp server
    chassis(work_dir, tftp, target)
    lan(work_dir, tftp, target)
    power(work_dir, tftp, target)
    event(work_dir, tftp, target)
    controller(work_dir, tftp, target)
    sdr(work_dir, tftp, target)
    sensor(work_dir, tftp, target)
    fru(work_dir, tftp, target)
    sel(work_dir, tftp, target)
    pef(work_dir, tftp, target)
    user(work_dir, tftp, target)
    channel(work_dir, tftp, target)
    session(work_dir, tftp, target)
    firmware(work_dir, tftp, target)
    fabric(work_dir, tftp, target)

    print_ubootenv(work_dir, tftp, target)

    print_cdb(target)
    print_registers(target)

def ipmitool(target, cmd):
    """ Run an ipmitool command on the target """
    ipmitool_args = cmd.split()
    try:
        return target.ipmitool_command(ipmitool_args)
    except Exception as e:
        return "%s: %s" % (e.__class__.__name__, e)

def chassis(work_dir, tftp, target):
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

def lan(work_dir, tftp, target):
    """ Print LAN information. """
    print '[ IPMI LAN Configuration ]'
    print ipmitool(target, 'lan print') + '\n'
    print '[ IPMI LAN Alerts ]'
    print ipmitool(target, 'lan alert print') + '\n'
    print '[ IPMI LAN Stats ]'
    print ipmitool(target, 'lan stats get') + '\n'

def power(work_dir, tftp, target):
    """ If there were power commands that it makes sense to issue, they would
    be here. """
    pass

def event(work_dir, tftp, target):
    """ If there were event commands that it makes sense to issue, they would
    be here. """
    pass

def controller(work_dir, tftp, target):
    """ Print management controller information. """
    print '[ IPMI BMC GUID ]'
    print ipmitool(target, 'mc guid') + '\n'
    #print '[ IPMI BMC Watchdog Timer ]'
    #print ipmitool(target, 'mc watchdog get') + '\n'
    print '[ IPMI BMC Global Enables ]'
    print ipmitool(target, 'mc getenables') + '\n'

def sdr(work_dir, tftp, target):
    """ Print sensor data record information. """
    print '[ IPMI Sensor Description Records ]'
    print ipmitool(target, 'sdr') + '\n'

def sensor(work_dir, tftp, target):
    """ Print sensor information """
    print '[ IPMI Sensors ]'
    print ipmitool(target, 'sensor') + '\n'

def fru(work_dir, tftp, target):
    """ Print FRU information. """
    print '[ IPMI FRU data records ]'
    print ipmitool(target, 'fru') + '\n'

def sel(work_dir, tftp, target):
    """ Print event log. """
    print '[ IPMI System Event Log ]'
    print ipmitool(target, 'sel') + '\n'

def pef(work_dir, tftp, target):
    """ Print PEF information. """
    print '[ IPMI Platform Event Filters ]'
    print ipmitool(target, 'pef') + '\n'

def user(work_dir, tftp, target):
    """ Print user information. """
    print '[ IPMI Users ]'
    print ipmitool(target, 'user list') + '\n'

def session(work_dir, tftp, target):
    """ Print session information. """
    print '[ IPMI Sessions Info ]'
    print ipmitool(target, 'session info all') + '\n'

def channel(work_dir, tftp, target):
    """ Print channel information. """
    #print '[ IPMI Channel Access ]'
    #print ipmitool(target, 'channel getaccess')
    print '[ IPMI Channel Info ]'
    print ipmitool(target, 'channel info') + '\n'
    #print '[ IPMI Channel Ciphers ]'
    #print ipmitool(target, 'channel getciphers')

def firmware(work_dir, tftp, target):
    """ Print firmware information. """
    print '[ IPMI Firmware Info ]'
    print ipmitool(target, 'cxoem fw info') + '\n'

def fabric(work_dir, tftp, target):
    """ Print the fabric-related data. """
    print '[ CXOEM Fabric Data ]'

    ipinfo = []
    try:
        ipinfo = target.get_ipinfo(work_dir, tftp)
        for entry in ipinfo:
            print 'Node %i: %s' % entry
    except Exception as e:
        print '%s: %s' % (e.__class__.__name__, e)

    try:
        macaddrs = target.get_macaddrs(work_dir, tftp)
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


def print_ubootenv(work_dir, tftp, target):
    print '[ U-Boot Environment ]'
    try:
        ubootenv = target.get_ubootenv(work_dir, tftp)
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
        print ipmitool(target, 'cxoem data cdb read 64 %s' % cid) + '\n'


def print_registers(target, registers=None):
    """ Print info for each register. """
    if registers == None:
        registers = resource_string('cxmanage', 'data/registers').split()

    print '[ Memory dump ]'
    for register in registers:
        output = ipmitool(target, 'cxoem data mem read 4 %s' % register)
        lines = [x for x in output.split('\n') if x.startswith('Value')]
        if len(lines) == 1:
            print 'Memory address %s: %s' % (register,
                    lines[0].partition(':')[2].rstrip().lstrip())
        else:
            print 'Memory address %s: failed to read' % register

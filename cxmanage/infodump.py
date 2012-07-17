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

def ipmitool(target, cmd):
    """ Run an ipmitool command on the target """
    ipmitool_args = cmd.split()
    try:
        target.ipmitool_command(ipmitool_args)
    except Exception as e:
        print "%s: %s" % e.__class__.__name__, e

def chassis(work_dir, tftp, target):
    """ Print Chassis information. """
    print '[ IPMI Chassis status ]'
    ipmitool(target, 'chassis status')
    print '[ IPMI Chassis Power status ]'
    ipmitool(target, 'chassis power status')
    #print '[ IPMI Chassis Restart Cause ]'
    #print ipmitool(args, 'chassis restart-cause')
    print '[ CXOEM Info ]'
    ipmitool(target, 'cxoem info basic')
    ipmitool(target, 'cxoem info partnum')
    ipmitool(target, 'cxoem info chassis')
    ipmitool(target, 'cxoem info node')
    print '[ IPMI Chassis Boot parameters ]'
    ipmitool(target, 'chassis bootparam get 0')
    ipmitool(target, 'chassis bootparam get 1')
    ipmitool(target, 'chassis bootparam get 2')
    ipmitool(target, 'chassis bootparam get 3')
    ipmitool(target, 'chassis bootparam get 4')
    ipmitool(target, 'chassis bootparam get 5')
    ipmitool(target, 'chassis bootparam get 6')
    ipmitool(target, 'chassis bootparam get 7')

def lan(work_dir, tftp, target):
    """ Print LAN information. """
    print '[ IPMI LAN Configuration ]'
    ipmitool(target, 'lan print')
    print '[ IPMI LAN Alerts ]'
    ipmitool(target, 'lan alert print')
    print '[ IPMI LAN Stats ]'
    ipmitool(target, 'lan stats get')

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
    ipmitool(target, 'mc guid')
    #print '[ IPMI BMC Watchdog Timer ]'
    #ipmitool(target, 'mc watchdog get')
    print '[ IPMI BMC Global Enables ]'
    ipmitool(target, 'mc getenables')

def sdr(work_dir, tftp, target):
    """ Print sensor data record information. """
    print '[ IPMI Sensor Description Records ]'
    ipmitool(target, 'sdr')

def sensor(work_dir, tftp, target):
    """ Print sensor information """
    print '[ IPMI Sensors ]'
    ipmitool(target, 'sensor')

def fru(work_dir, tftp, target):
    """ Print FRU information. """
    print '[ IPMI FRU data records ]'
    ipmitool(target, 'fru')

def sel(work_dir, tftp, target):
    """ Print event log. """
    print '[ IPMI System Event Log ]'
    ipmitool(target, 'sel')

def pef(work_dir, tftp, target):
    """ Print PEF information. """
    print '[ IPMI Platform Event Filters ]'
    ipmitool(target, 'pef')

def user(work_dir, tftp, target):
    """ Print user information. """
    print '[ IPMI Users ]'
    ipmitool(target, 'user list')

def session(work_dir, tftp, target):
    """ Print session information. """
    print '[ IPMI Sessions Info ]'
    ipmitool(target, 'session info all')

def channel(work_dir, tftp, target):
    """ Print channel information. """
    #print '[ IPMI Channel Access ]'
    #ipmitool(target, 'channel getaccess')
    print '[ IPMI Channel Info ]'
    ipmitool(target, 'channel info')
    #print '[ IPMI Channel Ciphers ]'
    #ipmitool(target, 'channel getciphers')

def firmware(work_dir, tftp, target):
    """ Print firmware information. """
    print '[ IPMI Firmware Info ]'
    ipmitool(target, 'cxoem fw info')

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
        sys.stdout.write('Node %i, netmask: ' % node_id)
        sys.stdout.flush()
        ipmitool(target, 'cxoem fabric get netmask node %i' % node_id)
        sys.stdout.write('Node %i, defgw: ' % node_id)
        sys.stdout.flush()
        ipmitool(target, 'cxoem fabric get defgw node %i' % node_id)
        sys.stdout.write('Node %i, ipsrc: ' % node_id)
        sys.stdout.flush()
        ipmitool(target, 'cxoem fabric get ipsrc node %i' % node_id)


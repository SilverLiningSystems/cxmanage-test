"""Calxeda: fabric.py"""


# Copyright (c) 2012-2013, Calxeda Inc.
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

from cxmanage_api.cli import get_tftp, get_nodes, run_command


def ipinfo_command(args):
    """get ip info from a cluster or host"""
    args.all_nodes = False

    tftp = get_tftp(args)
    nodes = get_nodes(args, tftp)

    if not args.quiet:
        print "Getting IP addresses..."

    results, _ = run_command(args, nodes, "get_fabric_ipinfo")

    for node in nodes:
        if node in results:
            print 'IP info from %s' % node.ip_address
            for node_id, node_address in sorted(results[node].items()):
                print 'Node %s: %s' % (node_id, node_address)
            print

    return 0


def macaddrs_command(args):
    """get mac addresses from a cluster or host"""
    args.all_nodes = False

    tftp = get_tftp(args)
    nodes = get_nodes(args, tftp)

    if not args.quiet:
        print "Getting MAC addresses..."
    results, errors = run_command(args, nodes, "get_fabric_macaddrs")

    for node in nodes:
        if node in results:
            print "MAC addresses from %s" % node.ip_address
            for node_id in sorted(results[node]):
                for port in results[node][node_id]:
                    for mac_address in results[node][node_id][port]:
                        print "Node %s, Port %i: %s" % (node_id, port,
                                mac_address)
            print

    if not args.quiet and errors:
        print "Some errors occured during the command.\n"

    return len(errors) == 0


def partition_config_command(args):
    """get partition config from nodes"""
    args.all_nodes = False

    tftp = get_tftp(args)
    nodes = get_nodes(args, tftp)

    if not args.quiet:
        print "Getting partition config..."
    results, errors = run_command(
        args, nodes, "run_fabric_tftp_command", "fabric_info_partition_config"
    )

    for node in nodes:
        if node in results:
            print "[ Partition config from %s ]" % node.ip_address
            print results[node].strip()
            print

    if not args.quiet and errors:
        print "Some errors occured during the command.\n"

    return len(errors) == 0


def uplink_info_command(args):
    """get uplink info from nodes"""
    args.all_nodes = False

    tftp = get_tftp(args)
    nodes = get_nodes(args, tftp)

    if not args.quiet:
        print "Getting uplink info..."
    results, errors = run_command(
        args, nodes, "run_fabric_tftp_command", "fabric_config_get_uplink_info"
    )

    for node in nodes:
        if node in results:
            print "[ Uplink info from %s ]" % node.ip_address
            print results[node].strip()
            print

    if not args.quiet and errors:
        print "Some errors occured during the command.\n"

    return len(errors) == 0


def uplinks_command(args):
    """get uplinks from nodes"""
    args.all_nodes = False

    tftp = get_tftp(args)
    nodes = get_nodes(args, tftp)

    if not args.quiet:
        print "Getting uplinks..."
    results, errors = run_command(
        args, nodes, "run_fabric_tftp_command", "fabric_config_get_uplinks"
    )

    for node in nodes:
        if node in results:
            print "[ Uplinks from %s ]" % node.ip_address
            print results[node].strip()
            print

    if not args.quiet and errors:
        print "Some errors occured during the command.\n"

    return len(errors) == 0


def networks_command(args):
    """get networks from nodes"""
    args.all_nodes = False

    tftp = get_tftp(args)
    nodes = get_nodes(args, tftp)

    if not args.quiet:
        print "Getting networks..."
    results, errors = run_command(
        args, nodes, "run_fabric_tftp_command", "fabric_config_get_networks"
    )

    for node in nodes:
        if node in results:
            print "[ Networks from %s ]" % node.ip_address
            print results[node].strip()
            print

    if not args.quiet and errors:
        print "Some errors occured during the command.\n"

    return len(errors) == 0

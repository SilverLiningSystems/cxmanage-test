#!/usr/bin/env python

# Copyright 2013 Calxeda, Inc. All Rights Reserved.


import os
import subprocess

from subprocess import call

from cxmanage import get_tftp, get_nodes, run_command


def coredump_command(args):
    """Get information pertaining to each node. This includes:
    IP addresses (ECME and server)
    Version info (like cxmanage info)
    MAC addresses
    Sensor readings
    Sensor data records
    Firmware info
    Boot order
    SELs (System Event Logs),
    Depth charts
    Routing Tables

    All nodes in the fabric should be powered on before running this command.

    This data will be written to a set of files. Each node will get its own
    file. All of these files will be archived and saved to the user's current
    directory.

    Internally, this command is called from:
    ~/virtual_testenv/workspace/cx_manage_util/scripts/cxmanage
    """

    tftp = get_tftp(args)
    nodes = get_nodes(args, tftp)

    temp_dir = "coredump"

    try:
        os.mkdir(temp_dir)
    except:
        """ Create a new directory with a unique name. The number
        associated with the directory (e.g. the "5" in "coredump5/")
        should match the number of the tar file (e.g. "coredump5.tar").

        """
        temp_dir, _ = get_unused_directory_and_file_names(".", "coredump.tar")

        os.mkdir(temp_dir)

    os.chdir(temp_dir)

    quiet = args.quiet

    write_ip_addresses(args, nodes)

    if not quiet:
        print("Getting boot order...")
    write_boot_order(args, nodes)

    if not quiet:
        print("Getting version information...")
    write_version_info(args, nodes)

    if not quiet:
        print("Getting MAC addresses...")
    write_mac_addrs(args, nodes)

    if not quiet:
        print("Getting sensor information...")
    write_sensor_info(args, nodes)
    print("Done!")

    if not quiet:
        print("Getting sensor data records...")
    write_sdr(args, nodes)
    print("Done!")

    if not quiet:
        print("Getting firmware information...")
    write_fwinfo(args, nodes)

    if not quiet:
        print("Getting system event logs...")
    write_sel(args, nodes)
    print("Done!")

    if not quiet:
        print("Getting depth charts...")
    write_depth_chart(args, nodes)

    if not quiet:
        print("Getting routing tables...")
    write_routing_table(args, nodes)

    # Archive the files
    os.chdir("..")
    archive(temp_dir)

    # The original files are already archived.
    delete_files(temp_dir)

    return 0


def write_ip_addresses(args, nodes):
    """ Write the ECME and server IP addresses for each node
    to their respective files.

    """
    ip_discover_results, ip_discover_errors = run_command(
        args,
        nodes,
        'get_server_ip')

    if (len(ip_discover_errors) > 0 and (not args.quiet)):
        print("WARNING: Error discovering server IP addresses on "
              "the following nodes:")
        for error in ip_discover_errors:
            print(node_ip(error))

    for node in nodes:
        write_to_file(
            node,
            ["Node " + str(node.node_id)],
            False
        )
        
        if node in ip_discover_results:
            write_to_file(
                node,
                ["[ ECME : Server ]",
                 node_ip(node) + " : " + ip_discover_results[node]]
            )
        else:
            write_to_file(
                node,
                ["[ ECME : Server ]",
                 node_ip(node) + " : (Unknown)"]
            )


def write_version_info(args, nodes):
    """ Write the version info (like cxmanage info) for each node
    to their respective files.

    """
    info_results, info_errors = run_command(args, nodes, "get_versions")

    # This will be used when writing version info to file
    components = [
        ("ecme_version", "ECME version"),
        ("cdb_version", "CDB version"),
        ("stage2_version", "Stage2boot version"),
        ("bootlog_version", "Bootlog version"),
        ("a9boot_version", "A9boot version"),
        ("uboot_version", "Uboot version"),
        ("ubootenv_version", "Ubootenv version"),
        ("dtb_version", "DTB version")
    ]

    for node in nodes:
        lines = []  # The lines of text to write to file
        # \n is used here to give a blank line before this section
        lines.append(
            "\n[ Version Info for Node " +
            str(node.node_id) + " ]"
        )

        if node in info_results:
            info_result = info_results[node]
            lines.append(
                "Hardware version   : %s" %
                info_result.hardware_version
                )
            lines.append(
                "Firmware version   : %s" %
                info_result.firmware_version
                )
            for var, description in components:
                if hasattr(info_result, var):
                    version = getattr(info_result, var)
                    lines.append("%s: %s" % (description.ljust(19), version))
        else:
            lines.append("No version information could be found.")

        write_to_file(node, lines)


def write_mac_addrs(args, nodes):
    """ Write the MAC addresses for each node to their respective files. """
    mac_addr_results, mac_addr_errors = run_command(
        args,
        nodes,
        "get_fabric_macaddrs"
        )

    for node in nodes:
        lines = []  # Lines of text to write to file
        # \n is used here to give a blank line before this section
        lines.append("\n[ MAC Addresses for Node " + str(node.node_id) + " ]")

        if node in mac_addr_results:
            for port in mac_addr_results[node][node.node_id]:
                for mac_address in mac_addr_results[node][node.node_id][port]:
                    lines.append("Node %i, Port %i: %s" %
                                (node.node_id, port, mac_address)
                                )
        else:
            lines.append("\nWARNING: No MAC addresses found!")
        write_to_file(node, lines)


def write_sensor_info(args, nodes):
    """ Write sensor information for each node to their respective files. """
    for node in nodes:
        lines = []  # Lines of text to write to file
        # \n is used here to give a blank line before this section
        lines.append("\n[ Sensors for Node " + str(node.node_id) + " ]")

        try:
            sensor_command = "ipmitool sensor -I lanplus -H " + \
                node_ip(node) + " -U admin -P admin list -v"
            sensor_call = subprocess.Popen(
                sensor_command.split(),
                stdout=subprocess.PIPE
                )
            sensor_info = sensor_call.communicate()[0]
            lines.append(sensor_info)
        except Exception as e:
            lines.append("Could not get sensor info! " + str(e))
            if not args.quiet:
                print("Failed to get sensor information for " + node_ip(node))
        write_to_file(node, lines)


def write_sdr(args, nodes):
    """ Write the sensor data record for each node to their
    respective files.

    """
    for node in nodes:
        lines = []  # Lines of text to write to file
        # \n is used here to give a blank line before this section
        lines.append(
            "\n[ Sensor Data Record for Node " + str(
                node.node_id) + " ]")

        try:
            sdr_command = "ipmitool sdr -I lanplus -H " + \
                node_ip(node) + " -U admin -P admin info"
            sdr_call = subprocess.Popen(
                sdr_command.split(),
                stdout=subprocess.PIPE
                )
            sdr = sdr_call.communicate()[0]
            lines.append(sdr)
        except Exception as e:
            lines.append("Could not get SDR! " + str(e))
            if not args.quiet:
                print("Failed to get sensor data record for " + node_ip(node))
        write_to_file(node, lines)


def write_fwinfo(args, nodes):
    """ Write information about each node's firware partitions
    to its respective file.

    """
    results, errors = run_command(args, nodes, "get_firmware_info")

    for node in nodes:
        lines = []  # Lines of text to write to file
        # \n is used here to give a blank line before this section
        lines.append("\n[ Firmware Info for Node " + str(node.node_id) + " ]")

        if node in results:
            for partition in results[node]:
                lines.append("\nPartition : %s" % partition.partition)
                lines.append("Type      : %s" % partition.type)
                lines.append("Offset    : %s" % partition.offset)
                lines.append("Size      : %s" % partition.size)
                lines.append("Priority  : %s" % partition.priority)
                lines.append("Daddr     : %s" % partition.daddr)
                lines.append("Flags     : %s" % partition.flags)
                lines.append("Version   : %s" % partition.version)
                lines.append("In Use    : %s" % partition.in_use)
        else:
            lines.append("Could not get firmware info!")
        write_to_file(node, lines)


def write_boot_order(args, nodes):
    """ Write the boot order of each node to their respective files. """
    results, boot_order_errors = run_command(args, nodes, "get_boot_order")

    for node in nodes:
        lines = []  # Lines of text to write to file
        # \n is used here to give a blank line before this section
        lines.append("\n[ Boot Order for Node " + str(node.node_id) + " ]")

        if node in results:
            lines.append(", ".join(results[node]))
        else:
            lines.append("Could not get boot order!")

        write_to_file(node, lines)


def write_sel(args, nodes):
    """ Write the SEL for each node to their respective files. """
    for node in nodes:
        lines = []  # Lines of text to write to file
        # \n is used here to give a blank line before this section
        lines.append(
            "\n[ System Event Log for Node " + str(
                node.node_id) + " ]")

        try:
            sel_command = "ipmitool sel -I lanplus -H " + node_ip(node) + \
                " -U admin -P admin list"
            sel_call = subprocess.Popen(
                sel_command.split(),
                stdout=subprocess.PIPE
                )
            sel = sel_call.communicate()[0]
            lines.append(sel)
        except Exception as e:
            lines.append("Could not get SEL! " + str(e))
            if not args.quiet:
                print("Failed to get system event log for " + node_ip(node))

        write_to_file(node, lines)


def write_depth_chart(args, nodes):
    """ Write the depth chart for each node to their respective files. """
    depth_results, depth_errors = run_command(args, nodes, "get_depth_chart")

    for node in nodes:
        lines = []  # Lines of text to write to file
        # \n is used here to give a blank line before this section
        lines.append("\n[ Depth Chart for Node " + str(node.node_id) + " ]")

        if node in depth_results:
            depth_chart = depth_results[node]
            for key in depth_chart:
                subchart = depth_chart[key]
                lines.append("To node " + str(key))
                for subkey in subchart:
                    lines.append("  " + str(subkey) +
                                 " : " + str(subchart[subkey])
                                )
        else:
            lines.append("Could not get depth chart!")

        write_to_file(node, lines)


def write_routing_table(args, nodes):
    """ Write the routing table for each node to their respective files. """
    routing_results, routing_errors = run_command(
        args, nodes, "get_routing_table")

    for node in nodes:
        lines = []  # Lines of text to write to file
        # \n is used here to give a blank line before this section
        lines.append("\n[ Routing Table for Node " + str(node.node_id) + " ]")

        if node in routing_results:
            table = routing_results[node]
            for node_to in table:
                lines.append(str(node_to) + " : " + str(table[node_to]))
        else:
            lines.append("Could not get routing table!")

        write_to_file(node, lines)


def write_to_file(node, toWrite, add_newlines=True):
    """ Append toWrite to an info file for every node in nodes.

    :param node: Node object to write about
    :type node: Nobe object
    :param toWrite: Text to write to the files
    :type toWrite: List of strings
    :
param add_newlines: Whether to add newline characters before
    every item in toWrite. True by default. True will add newline
    characters.
    :type add_newlines: bool

    """

    with open("node" + str(node.node_id) + ".txt", 'a') as file:
        for line in toWrite:
            if add_newlines:
                file.write("\n" + line)
            else:
                file.write(line)


def node_ip(node):
    """ Return a string containing the given node's ECME IP address.
    :returns: A string containing the node's ECME IP address.
    :rtype: string
    :param node: The node to get an IP address from.
    :type node: Node object

    """
    return str(node)[6:]


def delete_files(directory):
    """ Remove all files inside directory, and directory itself. """
    command = "rm -r " + directory
    call(command.split())


def archive(directory_to_archive):
    """ Creates a .tar containing everything in the directory_to_archive.
    The .tar is saved to the current directory under the same name as
    the directory, but with .tar appended.

    :param directory_to_archive: A path to the directory to be archived.
    :type directory_to_archive: string

    """

    make_tar_command = "tar -cf " + directory_to_archive + ".tar " + \
        directory_to_archive

    call(make_tar_command.split())
    print("Finished! One archive created:\n" + directory_to_archive + ".tar")


def get_unused_directory_and_file_names(directory, name):
    """ Given a directory and filename, determine an unused directory name
    and an unused file name that share the same name before any extensions.

    Returns: A list containing two strings: an unused directory name, and
    an unused file name.

    :param directory: A path to the directory to look in.
    :type directory: string
    :param name: The original name of a file, possibly including an extension
    :type name: string

    """
    dir_name, _, _ = name.partition(".")

    dir_number = 0
    file_number = 0

    while True:
        # Try to get an unused dir starting from file_number
        new_dir, dir_number = get_unused_name(directory, dir_name, file_number)

        # Try to get an unused name starting from dir_number
        new_file, file_number = get_unused_name(directory, name, dir_number)

        # dir_number and file_number always indicate unused names
        if dir_number == file_number:
            return [new_dir, new_file]


def get_unused_name(directory, name, number=0):
    """ Get a new filename. This new filename cannot be the same as any
    existing file in directory, and should be based off of name. name should
    contain one or zero periods, and should not start with a period.
    The return type is a list containing the new filename (string), and the
    number attached to it (int).

    :param directory: A path to directory
    :type directory: string
    :param name: The original name of a file, possibly with an extension
    :type name: string
    :param number: The number to start searching from
    :type number: int

    """
    name, dot, extension = name.partition('.')

    # Create a new string, similar to "name0.extension"
    destination = name + str(number) + dot + extension
    exit = False

    # Increment the number in name#.ext until we find an unused filename
    while exit == False:
        command = 'ls'

        a_call = subprocess.Popen(
            command.split(),
            stdout=subprocess.PIPE
        )
        call_result = a_call.communicate()[0]

        if destination in call_result:
            number = number + 1
            destination = name + str(number) + dot + extension
        else:
            exit = True

    return [destination, number]

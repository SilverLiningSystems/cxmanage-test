""" The controller object mediates between a UI and the application model.
In this case, the controller understands the model's container structure
and the objects it contains: tftp, images, targets and plans. """

import atexit
import os
import shutil
import tempfile
import time

from images import Images
from targets import Targets, Target
from tftp import Tftp
from simg import create_simg, verify_simg

class Controller:
    """ The controller class serves as a manager for all the internals of
    cx_manage_util. Scripts or UIs can build on top of this to provide an user
    interface. """

    def __init__(self):
        self._images = Images()
        self._targets = Targets()
        self._tftp = Tftp()
        self._work_dir = tempfile.mkdtemp(prefix="cxmanage-")
        atexit.register(self._cleanup)

###########################  TFTP-specific methods ###########################

    def set_internal_tftp_server(self, address=None, port=0):
        """ Set up a TFTP server to be hosted locally """
        self._tftp.set_internal_server(self._work_dir, address, port)

    def set_external_tftp_server(self, address, port=69):
        """ Set up a remote TFTP server """
        self._tftp.set_external_server(address, port)

    def restart_tftp_server(self):
        """ Restart the TFTP server """
        self._tftp.restart_server()

    def get_tftp_address(self):
        """ Return the address of the external TFTP server """
        return self._tftp.get_address()

    def get_tftp_port(self):
        """ Return the port used by the internal TFTP server"""
        return self._tftp.get_port()

    def tftp_get(self, tftppath, localpath):
        """ Download a file from the TFTP server """
        self._tftp.get_file(tftppath, localpath)

    def tftp_put(self, tftppath, localpath):
        """ Upload a file to the TFTP server """
        self._tftp.put_file(tftppath, localpath)

###########################  Images-specific methods ##########################

    def add_image(self,
                  image_name,
                  image_type,
                  filename,
                  force_simg=False,
                  skip_simg=False,
                  version=0,
                  daddr=0,
                  skip_crc32=False):
        """ Add an image to our collection """
        if force_simg or not (skip_simg or verify_simg(filename)):
            new_path = self._work_dir + "/" + os.path.basename(filename) + ".simg"
            create_simg(filename, new_path, version=version,
                    daddr=daddr, skip_crc32=skip_crc32)
        else:
            new_path = filename

        self._images.add_image(image_name, image_type, new_path)

###########################  Targets-specific methods #########################

    def add_target(self, group, address, username, password):
        """ Add the target to the list of targets for the group.
        Eliminate duplicates."""
        self._targets.add_target(group, address, username, password)

    def delete_group(self, group):
        """ Delete the specified target group """
        self._targets.delete_group(group)

    def group_exists(self, group):
        """ Return true if 'group' is the name of a target group contained
        in the model."""
        return self._targets.group_exists(group)

    def get_targets_in_range(self, start, end):
        """ Return a list of addresses in the given IP range """
        try:
            # Convert startaddr to int
            start_bytes = map(int, start.split("."))
            start_i = ((start_bytes[0] << 24) | (start_bytes[1] << 16)
                    | (start_bytes[2] << 8) | (start_bytes[3]))

            # Convert endaddr to int
            end_bytes = map(int, end.split("."))
            end_i = ((end_bytes[0] << 24) | (end_bytes[1] << 16)
                    | (end_bytes[2] << 8) | (end_bytes[3]))

            # Get ip addresses in range
            addresses = []
            for i in range(start_i, end_i + 1):
                address_bytes = [(i >> (24 - 8 * x)) & 0xff for x in range(4)]
                address = (str(address_bytes[0]) + "." + str(address_bytes[1])
                        + "." + str(address_bytes[2]) + "."
                        + str(address_bytes[3]))

                addresses.append(address)

            return addresses

        except IndexError:
            raise ValueError

    def get_targets_from_fabric(self, address, username, password):
        """ Get a list of targets reported by fabric """

        # Create initial target
        target = Target(address, username, password)

        # Retrieve ip_info file
        target.get_fabric_ipinfo(self._tftp, "ip_info.txt")
        # TODO: don't sleep on failure.
        time.sleep(1) # must delay before retrieving file
        ip_info_path = self._work_dir + "/ip_info.txt"
        self.tftp_get("ip_info.txt", ip_info_path)

        # Parse addresses from ip_info file
        addresses = []
        ip_info_file = open(ip_info_path, "r")
        for line in ip_info_file:
            address = line.split()[-1]

            # TODO: question this -- is it necessary/proper?
            if address != "0.0.0.0":
                addresses.append(address)

        ip_info_file.close()

        return addresses

#########################    Execution methods    #########################

    def power_command(self, group, command):
        """ Send the given power command to all targets in group """
        successes = []
        errors = []
        targets = self._targets.get_targets_in_group(group)
        for target in targets:
            try:
                target.power_command(command)
                successes.append(target._address)
            except Exception as e:
                errors.append("%s: %s" % (target._address, e))

        # Print successful hosts
        if len(successes) > 0:
            print "\nPower %s command executed successfully on the following hosts" % command
            for host in successes:
                print host

        # Print errors
        if len(errors) > 0:
            print "\nThe following errors occured"
            for error in errors:
                print error

    def power_status(self, group):
        """ Retrieve power status from all targets in group """
        results = []
        targets = self._targets.get_targets_in_group(group)
        for target in targets:
            try:
                status = target.power_status()
                results.append("%s: %s" % (target._address, status))
            except Exception as e:
                results.append("%s: %s" % (target._address, e))

        # Print results
        if len(results) > 0:
            print "\nPower status"
            for result in results:
                print result
        else:
            print "\nERROR: Failed to retrieve power status info"

    def update_firmware(self, group, image, slot_arg):
        """ Send firmware update commands to all targets in group. """

        # Upload image to TFTP
        try:
            image_type = self._images.get_image_type(image)
            full_filename = os.path.abspath(self._images.get_image_filename(image))
            filename = os.path.basename(full_filename)
            self.tftp_put(filename, full_filename)
        except Exception as e:
            # Failed to upload to TFTP
            print "\nERROR: Failed to upload to TFTP server"
            print "No hosts were updated."
            return

        # Update firmware on all targets
        successes = []
        errors = []
        targets = self._targets.get_targets_in_group(group)
        for target in targets:
            try:
                target.update_firmware(self._tftp,
                        image_type, filename, slot_arg)
                successes.append(target._address)
            except Exception as e:
                errors.append("%s: %s" % (target._address, e))

        # Print successful hosts
        if len(successes) > 0:
            print "\nFirmware updated successfully on the following hosts"
            for host in successes:
                print host

        # Print errors
        if len(errors) > 0:
            print "\nThe following errors occured"
            for error in errors:
                print error

    def mc_reset(self, group):
        """ Send the given power command to all targets in group """
        successes = []
        errors = []
        targets = self._targets.get_targets_in_group(group)
        for target in targets:
            try:
                target.mc_reset()
                successes.append(target._address)
            except Exception as e:
                errors.append("%s: %s" % (target._address, e))

        # Print errors
        if len(errors) > 0:
            print "\nThe following errors occured"
            for error in errors:
                print error

    def _cleanup(self):
        """ Clean up temporary files """
        shutil.rmtree(self._work_dir)

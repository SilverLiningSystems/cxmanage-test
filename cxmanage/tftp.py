#Copyright 2012 Calxeda, Inc.  All Rights Reserved.

""" Holds state about the tftp service to be used by a calxeda update
application. """

import atexit
import logging
import os
import signal
import shutil
import socket
import subprocess
import tempfile

from cxmanage import CxmanageError

from tftpy import TftpClient, TftpServer, setLogLevel
from tftpy.TftpShared import TftpException

class InternalTftp:
    """ Internal TFTP server """

    def __init__(self, address=None, port=0, verbosity=1):
        self.tftp_dir = tempfile.mkdtemp(prefix="cxmanage-tftp-")
        self.server = os.fork()
        if self.server == 0:
            TftpServer(self.tftp_dir).listen(address, port)
            os._exit(0)
        atexit.register(self.kill)

        if port != 0:
            self.port = port
        else:
            self.port = self._discover_port()

        if verbosity <= 1:
            setLogLevel(logging.CRITICAL)

    def kill(self):
        """ Kill the server if it's still up """
        if self.server != None:
            os.kill(self.server, signal.SIGTERM)
            self.server = None
        if os.path.exists(self.tftp_dir):
            shutil.rmtree(self.tftp_dir)

    def get_address(self, relative_host=None):
        """ Return the address of this server.

        If this is an internal server, and we're given a relative host,
        then discover our address to them automatically. """

        if relative_host == None:
            # TODO: make a guess
            return None
        else:
            # Get our address by opening a socket to the host
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect((relative_host, self.port))
            address = s.getsockname()[0]
            s.close()
            return address

    def get_port(self):
        """ Return the listening port of this server """
        return self.port

    def get_file(self, tftppath, localpath):
        """ Download a file from the tftp server """
        try:
            tftppath = "%s/%s" % (self.tftp_dir, tftppath)
            if not os.path.exists(tftppath):
                raise CxmanageError("File does not exist on TFTP server")
            shutil.copy(tftppath, localpath)
        except IOError:
            raise CxmanageError("Failed to download file from TFTP server")

    def put_file(self, localpath, tftppath):
        """ Upload a file to the tftp server """
        try:
            if not os.path.exists(localpath):
                raise CxmanageError("File does not exist on local disk")
            tftppath = "%s/%s" % (self.tftp_dir, tftppath)
            shutil.copy(localpath, tftppath)
        except IOError:
            raise CxmanageError("Failed to upload file to TFTP server")

    def _discover_port(self):
        """ Discover what port an internal server is bound to.
        This uses the 'lsof' command line utility """
        try:
            command = "lsof -p%i -a -i4" % self.server
            output = subprocess.check_output(command.split()).rstrip()
            line = output.split("\n")[-1]
            port = int(line.split()[8].split(":")[1])
            return port
        except (OSError, ValueError):
            raise CxmanageError("Failed to discover internal TFTP port")

class ExternalTftp:
    """ External TFTP server """

    def __init__(self, address, port=69, verbosity=1):
        self.client = TftpClient(address, port)
        self.address = address
        self.port = port

        if verbosity <= 1:
            setLogLevel(logging.CRITICAL)

    def kill(self):
        """ Do nothing """
        pass

    def get_address(self, relative_host=None):
        """ Return the address of this server. """
        return self.address

    def get_port(self):
        """ Return the listening port of this server """
        return self.port

    def get_file(self, tftppath, localpath):
        """ Download a file from the tftp server """
        try:
            self.client.download(tftppath, localpath)
        except TftpException:
            raise CxmanageError("Failed to download file from TFTP server")

    def put_file(self, localpath, tftppath):
        """ Upload a file to the tftp server """
        try:
            self.client.upload(tftppath, localpath)
        except TftpException:
            raise CxmanageError("Failed to upload file to TFTP server")

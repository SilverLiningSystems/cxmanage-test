#Copyright 2012 Calxeda, Inc.  All Rights Reserved.

""" Holds state about the tftp service to be used by a calxeda update
application. """

import atexit
import os
import signal
import shutil
import socket
import subprocess

from cxmanage import CxmanageError

from tftpy import TftpClient, TftpServer
from tftpy.TftpShared import TftpException

class Tftp:
    """ Contains info about a remote or local TFTP server """

    def __init__(self):
        self._server = None
        self._client = None
        self._root_dir = None

        self._ipaddr = None
        self._port = None

        self._isinternal = False
        self._hasbeengood = False

        atexit.register(self.kill_server)

    def set_internal_server(self, root_dir, addr=None, port=0):
        """ Shut down any server that's currently running, then start an
        internal tftp server. """

        # Kill existing internal server
        self.kill_server()

        # Start tftp server
        self._server = os.fork()
        if self._server == 0:
            server = TftpServer(root_dir)
            server.listen(addr, port)
            os._exit(0)

        self._client = None
        self._root_dir = root_dir

        self._ipaddr = addr

        if port != 0:
            self._port = port
        else:
            self._port = self._discover_port()

        self._isinternal = True
        self._hasbeengood = False

    def set_external_server(self, addr, port=69):
        """ Shut down any server that's currently running, then set up a
        connection to an external tftp server. """

        # Kill existing internal server
        self.kill_server()

        self._root_dir = None
        self._server = None
        self._client = TftpClient(addr, port)

        self._ipaddr = addr
        self._port = port

        self._isinternal = False
        self._hasbeengood = False

    def kill_server(self):
        """ Kill the internal server if we're running one """
        if self._server != None:
            os.kill(self._server, signal.SIGTERM)
            self._server = None

    def get_address(self, relative_host=None):
        """ Return the address of this server.

        If this is an internal server, and we're given a relative host,
        then discover our address to them automatically. """

        # Get address relative to host
        if self._isinternal and relative_host != None:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect((relative_host, self._port))
            address = s.getsockname()[0]
            s.close()
            return address

        return self._ipaddr

    def get_port(self):
        """ Return the listening port of this server """
        return self._port

    def get_file(self, tftppath, localpath):
        """ Download a file from the tftp server """
        try:
            if self._isinternal:
                tftppath = self._root_dir + "/" + tftppath
                if not os.path.exists(tftppath):
                    raise CxmanageError("File does not exist on TFTP server")
                if tftppath != localpath:
                    shutil.copy(tftppath, localpath)
            else:
                self._client.download(tftppath, localpath)
        except (IOError, TftpException):
            raise CxmanageError("Failed to download file from TFTP server")

    def put_file(self, localpath, tftppath):
        """ Upload a file to the tftp server """
        try:
            if self._isinternal:
                tftppath = self._root_dir + "/" + tftppath
                if not os.path.exists(localpath):
                    raise CxmanageError("File does not exist on local disk")
                if tftppath != localpath:
                    shutil.copy(localpath, tftppath)
            else:
                self._client.upload(tftppath, localpath)
        except (IOError, TftpException):
            raise CxmanageError("Failed to upload file to TFTP server")

    def _discover_port(self):
        """ Discover what port an internal server is bound to.
        This uses the 'lsof' command line utility """
        try:
            command = "lsof -p%i -a -i4" % self._server
            output = subprocess.check_output(command.split()).rstrip()
            line = output.split("\n")[-1]
            port = int(line.split()[8].split(":")[1])
            return port
        except (OSError, ValueError):
            raise CxmanageError("Failed to discover internal TFTP port")

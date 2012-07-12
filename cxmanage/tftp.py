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


""" Holds state about the tftp service to be used by a calxeda update
application. """

import atexit
import logging
import os
import shutil
import socket
import tempfile
import threading

from cxmanage import CxmanageError

from tftpy import TftpClient, TftpServer, setLogLevel
from tftpy.TftpShared import TftpException

class InternalTftp(threading.Thread):
    """ Internal TFTP server """

    def __init__(self, address=None, port=0, verbosity=1):
        threading.Thread.__init__(self)
        self.daemon = True

        self.address = address
        self.port = port

        self.tftp_dir = tempfile.mkdtemp(prefix="cxmanage-tftp-")
        atexit.register(self._cleanup)

        self.server = TftpServer(self.tftp_dir)

        self.start()
        atexit.register(self._cleanup)

        if verbosity <= 1:
            setLogLevel(logging.CRITICAL)

    def run(self):
        """ Run the server, ignoring any exceptions """
        try:
            self.server.listen(self.address, self.port)
        except:
            pass

    def _cleanup(self):
        """ Clean up our resources on exit """
        if os.path.exists(self.tftp_dir):
            shutil.rmtree(self.tftp_dir)

    def get_address(self, relative_host=None):
        """ Return the address of this server.

        If this is an internal server, and we're given a relative host,
        then discover our address to them automatically. """

        if self.address != None or relative_host == None:
            return self.address
        else:
            # Get our address by opening a socket to the host
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect((relative_host, self.port))
            address = s.getsockname()[0]
            s.close()
            return address

    def get_port(self):
        """ Return the listening port of this server """
        if self.port == 0:
            while self.server.sock == None:
                pass
            port = self.server.sock.getsockname()[1]
        else:
            port = self.port

        return port

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

    def kill(self):
        """ Kill the server if it's still up """
        # this is really hacky -- kill the server by removing its socket
        if self.server != None:
            while self.server.sock == None:
                pass
            self.server.sock.close()
            self.server = None

        self._cleanup()

class ExternalTftp:
    """ External TFTP server """

    def __init__(self, address, port=69, verbosity=1):
        self.client = TftpClient(address, port)
        self.address = address
        self.port = port

        if verbosity <= 1:
            setLogLevel(logging.CRITICAL)

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

    def kill(self):
        """ Do nothing """
        pass

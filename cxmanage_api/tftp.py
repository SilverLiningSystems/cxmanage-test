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
"""Internal/External TFTP interfaces for command/response."""


import os
import sys
import atexit
import shutil
import socket
import logging
import traceback

from tftpy import TftpClient, TftpServer, setLogLevel
from threading import Thread
from tftpy.TftpShared import TftpException
from cxmanage_api import temp_dir


class InternalTftp(object):
    """Internally serves files using TFTP.
    
    >>> # Typical instantiation ...
    >>> from cxmanage_api.tftp import InternalTftp
    >>> i_tftp = InternalTftp()
    
    :param ip_address: Ip address for the Internal TFTP server to use.
    :type ip_address: string
    :param port: Port for the internal TFTP server.
    :type port: integer
    :param verbose: Flag to turn on additional messaging.
    :type verbose: boolean
    
    """

    def __init__(self, ip_address=None, port=0, verbose=True):
        """Default constructor for the InternalTftp class."""
        self.tftp_dir = temp_dir()
        self.verbose = verbose

        pipe = os.pipe()
        pid = os.fork()
        if (not pid):
            # Create a PortThread class only if needed ...
            class PortThread(Thread):
                """Thread that sends the port number through the pipe."""
                def run(self):
                    """Run function override."""
                    # Need to wait for the server to open its socket
                    while not server.sock:
                        pass
                    with os.fdopen(pipe[1], "w") as a_file:
                        a_file.write("%i\n" % server.sock.getsockname()[1])
            #
            # Create an Internal TFTP server thread
            #
            server = TftpServer(tftproot=self.tftp_dir)
            thread = PortThread()
            thread.start()
            try:
                if (self.verbose):
                    setLogLevel(logging.CRITICAL)
                # Start accepting connections ...
                server.listen(ip_address, port)

            except KeyboardInterrupt:
                # User @ keyboard cancelled server ...
                if (self.verbose):
                    traceback.format_exc()
            sys.exit(0)

        self.server = pid
        self.ip_address = ip_address
        with os.fdopen(pipe[0]) as a_fd:
            self.port = int(a_fd.readline())
        atexit.register(self.kill)

    def get_port(self):
        """Return the listening port of this server."""
        return self.port

    def get_address(self, relative_host=None):
        """Returns the ipv4 address of this server.
        If this is an internal server, and we're given a relative host ip,
        then discover our address to them automatically.

        :param relative_host: Ip address to the relative host.
        :type relative_host: string

        :return: The ipv4 address of this InternalTftpServer.
        :rtype: string
        """
        if ((self.ip_address != None) or (relative_host == None)):
            return self.ip_address
        else:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.connect((relative_host, self.port))
            ipv4 = sock.getsockname()[0]
            sock.close()
            return ipv4

    def kill(self):
        """Kills the InternalTftpServer."""
        if (self.server):
            os.kill(self.server, 15)
            self.server = None

    def get_file(self, src, dest):
        """Download a file from the tftp server to local_path.

        :param src: Path on the tftp_server.
        :type src: string
        :param dest: Path (on your machine) to copy the TFTP file to.
        :type dest: string

        :return: Whether the transfer was successful or not.
        :rtype: boolean
        """
        src = "%s/%s" % (self.tftp_dir, src)
        if (src != dest):
            try:
                # Ensure the file exists ...
                with open(src) as a_file:
                    a_file.close()
                shutil.copy(src, dest)

            except Exception:
                traceback.format_exc()
                raise
        return True

    def put_file(self, src, dest):
        """Upload a file from src to dest on the tftp server (path).

        :param src: Path to the local file to send to the TFTP server.
        :type src: string
        :param dest: Path to put the file to on the TFTP Server.
        :type dest: string

        :return: Whether the transfer was successful or not.
        :rtype: boolean
        """
        dest = "%s/%s" % (self.tftp_dir, dest)
        if (src != dest):
            try:
                # Ensure that the local file exists ...
                with open(src) as a_file:
                    a_file.close()
                shutil.copy(src, dest)

            except Exception:
                traceback.format_exc()
                raise
        return True


class ExternalTftp(object):
    """Defines a ExternalTftp server, essentially makes this class a client."""

    def __init__(self, ip_address, port=69, verbose=True):
        """Default constructor for this the ExternalTftp class.

        :param ip_address: Ip address of the TFTP server.
        :type ip_address: string
        :param port: Port to the External TFTP server.
        :type port: integer
        :param verbose: Flag to turn on verbose output (cmd/response).
        :type verbose: boolean
        """
        self.ip_address = ip_address
        self.port = port
        self.verbose = verbose

        if (self.verbose):
            setLogLevel(logging.CRITICAL)

    def get_address(self, relative_host=None):
        """Return the ip address of the ExternalTftp server."""
        del relative_host # Needed only for function signature.
        return self.ip_address

    def get_port(self):
        """Return the listening port of this server."""
        return self.port

    def get_file(self, src, dest):
        """Download a file from the ExternalTftp Server.

        :param src: The path to the file on the Tftp server.
        :type src: string
        :param dest: The local destination to copy the file to.
        :type dest: string
        """
        try:
            # NOTE: TftpClient is not threadsafe, so we create a unique
            # instance for each transfer.
            client = TftpClient(self.ip_address, self.port)
            client.download(output=dest, filename=src)

        except TftpException:
            if (self.verbose):
                traceback.format_exc()
            raise

    def put_file(self, src, dest):
        """ Upload a file to the tftp server """
        try:
            # NOTE: TftpClient is not threadsafe, so we create a unique
            # instance for each transfer.
            client = TftpClient(self.ip_address, self.port)
            client.upload(input=src, filename=dest)

        except TftpException:
            if (self.verbose):
                traceback.format_exc()
            raise


# End of file: ./tftp.py

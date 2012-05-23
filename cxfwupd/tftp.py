""" Holds state about the tftp service to be used by a calxeda update
application. """

import atexit, os, signal, shutil

from cxfwupd_resources import cxfwupd_resources
from tftpy import TftpClient, TftpServer

class tftp:

    def __init__(self):
        self._ipaddr = None
        self._interface = None
        self._port = None

        self._isinternal = False
        self._hasbeengood = False

        self._server = None
        self._client = None

        atexit.register(self.kill_server)

    def get_settings_str(self):
        """ Get tftp settings as a string """
        strings = cxfwupd_resources.get_strings('tftp')
        s = ''
        if self._ipaddr == None:
            s = strings['not-set']
        else:
            s = self._ipaddr + ':' + str(self._port)
            if self._isinternal:
                s += strings['internal-server']
            if not self._hasbeengood:
                res = self.is_reachable()
            if res:
                s += strings['is-reachable']
            else:
                if self._hasbeengood:
                    s += strings['know-good-once']
                else:
                    s += strings['not-reachable']
        return s

    def is_set(self):
        """ Return true if a server has been set """
        return self._ipaddr != None

    def is_internal(self):
        """ Return true if we're using an internal server """
        return self._isinternal

    def is_reachable(self):
        """ Attempt to reach the tftp server. Return true if the server was
        reached successfully. """
        if self._ipaddr != None:
            # Try sending and receiving something small. if successful,
            # set _hasbeengood and return True; otherwise return False
            return True
        return False

    def set_internal_server(self, interface, port):
        """ Shut down any server that's currently running, then start an
        internal tftp server. """

        # Kill existing internal server
        self.kill_server()

        # TODO: get _ipaddr properly
        self._ipaddr = "127.0.0.1"
        self._interface = interface
        self._port = port

        self._isinternal = True
        self._hasbeengood = False

        # Start tftp server
        self._server = os.fork()
        if self._server == 0:
            if not os.path.exists("tftp"):
                os.mkdir("tftp")
            server = TftpServer("tftp")
            server.listen(self._ipaddr, self._port)
            os._exit(0)

        self._client = TftpClient("127.0.0.1", self._port)

    def set_external_server(self, addr, port):
        """ Shut down any server that's currently running, then set up a
        connection to an external tftp server. """

        # Kill existing internal server
        self.kill_server()

        self._ipaddr = addr
        self._interface = None
        self._port = port

        self._isinternal = False
        self._hasbeengood = False

        self._server = None
        self._client = TftpClient(self._ipaddr, self._port)

    def restart_server(self):
        """ Reset the server model; this will also restart the server if it's
        internal. """
        if self._isinternal:
            self.set_internal_server(self._interface, self._port)
        else:
            self.set_external_server(self._ipaddr, self._port)

    def kill_server(self):
        """ Kill the internal server if we're running one """
        if self._server != None:
            os.kill(self._server, signal.SIGTERM)
            self._server = None

    def get_internal_server_interface(self):
        """ Return the interface used by the internal server """
        return self._interface

    def get_file(self, tftppath, localpath):
        """ Download a file from the tftp server """
        if self._isinternal:
            shutil.copy("tftp/" + tftppath, localpath)
        else:
            self._client.download(tftppath, localpath)

    def put_file(self, tftppath, localpath):
        """ Upload a file to the tftp server """
        if self._isinternal:
            shutil.copy(localpath, "tftp/" + tftppath)
        else:
            self._client.upload(tftppath, localpath)

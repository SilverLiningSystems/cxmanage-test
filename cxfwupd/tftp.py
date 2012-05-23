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
        return self._ipaddr != None

    def is_internal(self):
        return self._isinternal

    def is_reachable(self):
        """ Attempt to reach the tftp server """
        if self._ipaddr != None:
            # Try sending and receiving something small. if successful,
            # set _hasbeengood and return True; otherwise return False
            return True
        return False

    def set_internal_server(self, interface, port):
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
            sys._exit(0)

        self._client = TftpClient("127.0.0.1", self._port)

    def set_external_server(self, addr, port):
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
        if self._isinternal:
            self.set_internal_server(self._interface, self._port)
        else:
            self.set_external_server(self._ipaddr, self._port)

    def kill_server(self):
        if self._server != None:
            os.kill(self._server, signal.SIGTERM)

    def get_internal_server_interface(self):
        return self._interface

    def get_file(self, tftppath, localpath):
        if self._isinternal:
            shutil.copy("tftp/" + tftppath, localpath)
        else:
            self._client.download(tftp_path, localpath)

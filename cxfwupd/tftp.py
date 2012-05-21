""" Holds state about the tftp service to be used by a calxeda update
application. """

from cxfwupd_resources import cxfwupd_resources

class tftp:

    def __init__(self, ipaddr, port, isinternal):
        self._ipaddr = ipaddr
        try:
            self._port = int(port)
        except ValueError, TypeError:
            self._port = 69
        self._isinternal = isinternal
        self._hasbeengood = False

    def isReachable(self):
        if self._ipaddr:
            # Try sending and receiving something small. if successful,
            # set _hasbeengood and return True; otherwise return False
            return True
        return False

    def get_settings_str(self):
        strings = cxfwupd_resources.get_strings('tftp')
        s = ''
        if not self._ipaddr:
            s = strings['not-set']
        else:
            s = self._ipaddr + ':' + str(self._port)
            if self._isinternal:
                s += strings['internal-server']
            if not self._hasbeengood:
                res = self.isReachable()
            if (res):
                s += strings['is-reachable']
            else:
                if self._hasbeengood:
                    s += strings['know-good-once']
                else:
                    s += strings['not-reachable']
        return s

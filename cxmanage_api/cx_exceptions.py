"""Defines the custom exceptions used by the cxmanage_api project."""


class TimeoutError(Exception):
    """Raised when a timeout has been reached.

    >>> from cxmanage_api.cx_exceptions import TimeoutError

    :param msg: Exceptions message and details to return to the user.
    :type msg: string
    :raised: When a timeout has been reached.

    """

    def __init__(self, msg):
        """Default constructor for the TimoutError class."""
        super(TimeoutError, self).__init__()
        self.msg = msg

    def __str__(self):
        """String representation of this Exception class."""
        return self.msg


class NoPartitionError(Exception):
    """Raised when a partition is not found.

    >>> from cxmanage_api.cx_exceptions import NoPartitionError

    :param msg: Exceptions message and details to return to the user.
    :type msg: string
    :raised: When a partition is not found.

    """

    def __init__(self, msg):
        """Default constructor for the NoPartitionError class."""
        super(NoPartitionError, self).__init__()
        self.msg = msg

    def __str__(self):
        """String representation of this Exception class."""
        return self.msg


class NoIpInfoError(Exception):
    """Raised when the Ip Info cannot be retrieved from a node.

    >>> from cxmanage_api.cx_exceptions import NoIpInfoError

    :param msg: Exceptions message and details to return to the user.
    :type msg: string
    :raised: When the Ip Info cannot be retrieved from a node.

    """

    def __init__(self, msg):
        """Default constructor for the NoIpInfo class."""
        super(NoIpInfoError, self).__init__()
        self.msg = msg

    def __str__(self):
        """String representation of this Exception class."""
        return self.msg


class NoMacAddressError(Exception):
    """Raised when MAC adresses cannot be retrieved from a node.

    >>> from cxmanage_api.cx_exceptions import NoMacAddressError

    :param msg: Exceptions message and details to return to the user.
    :type msg: string
    :raised: When MAC adresses cannot be retrieved from a node.

    """

    def __init__(self, msg):
        """Default constructor for the NoAddressError class."""
        super(NoMacAddressError, self).__init__()
        self.msg = msg

    def __str__(self):
        """String representation of this Exception class."""
        return self.msg


class NoSensorError(Exception):
    """Raised when a sensor or sensors are not found.

    >>> from cxmanage_api.cx_exceptions import NoSensorError

    :param msg: Exceptions message and details to return to the user.
    :type msg: string
    :raised: When a sensor or sensors are not found.

    """

    def __init__(self, msg):
        """Default constructor for the NoSensorError class."""
        super(NoSensorError, self).__init__()
        self.msg = msg

    def __str__(self):
        """String representation of this Exception class."""
        return self.msg


class NoFirmwareInfoError(Exception):
    """Raised when the firmware info cannot be obtained from a node.

    >>> from cxmanage_api.cx_exceptions import NoFirmwareInfoError

    :param msg: Exceptions message and details to return to the user.
    :type msg: string
    :raised: When the firmware info cannot be obtained from a node.

    """

    def __init__(self, msg):
        """Default constructor for the NoFirmwareInfoError class."""
        super(NoFirmwareInfoError, self).__init__()
        self.msg = msg

    def __str__(self):
        """String representation of this Exception class."""
        return self.msg


class SocmanVersionError(Exception):
    """Raised when there is an error with the users socman version.

    >>> from cxmanage_api.cx_exceptions import SocmanVersionError

    :param msg: Exceptions message and details to return to the user.
    :type msg: string
    :raised: When there is an error with the users socman version.

    """

    def __init__(self, msg):
        """Default constructor for the SocmanVersionError class."""
        super(SocmanVersionError, self).__init__()
        self.msg = msg

    def __str__(self):
        """String representation of this Exception class."""
        return self.msg


class FirmwareConfigError(Exception):
    """Raised when there are slot/firmware version inconsistencies.

    >>> from cxmanage_api.cx_exceptions import FirmwareConfigError

    :param msg: Exceptions message and details to return to the user.
    :type msg: string
    :raised: When there are slot/firmware version inconsistencies.

    """

    def __init__(self, msg):
        """Default constructor for the FirmwareConfigError class."""
        super(FirmwareConfigError, self).__init__()
        self.msg = msg

    def __str__(self):
        """String representation of this Exception class."""
        return self.msg


class PriorityIncrementError(Exception):
    """Raised when the Priority on a SIMG image cannot be altered.

    >>> from cxmanage_api.cx_exceptions import PriorityIncrementError

    :param msg: Exceptions message and details to return to the user.
    :type msg: string
    :raised: When the Priority on a SIMG image cannot be altered.

    """

    def __init__(self, msg):
        """Default constructor for the PriorityIncrementError class."""
        super(PriorityIncrementError, self).__init__()
        self.msg = msg

    def __str__(self):
        """String representation of this Exception class."""
        return self.msg


class ImageSizeError(Exception):
    """Raised when the actual size of the image is not what is expected.

    >>> from cxmanage_api.cx_exceptions import ImageSizeError

    :param msg: Exceptions message and details to return to the user.
    :type msg: string
    :raised: When the actual size of the image is not what is expected.

    """

    def __init__(self, msg):
        """Default constructor for the ImageSizeError class."""
        super(ImageSizeError, self).__init__()
        self.msg = msg

    def __str__(self):
        """String representation of this Exception class."""
        return self.msg


class TransferFailure(Exception):
    """Raised when the transfer of a file has failed.

    >>> from cxmanage_api.cx_exceptions import TransferFailure

    :param msg: Exceptions message and details to return to the user.
    :type msg: string
    :raised: When the transfer of a file has failed.

    """

    def __init__(self, msg):
        """Default constructor for the TransferFailure class."""
        super(TransferFailure, self).__init__()
        self.msg = msg

    def __str__(self):
        """String representation of this Exception class."""
        return self.msg


class InvalidImageError(Exception):
    """Raised when an image is not valid. (i.e. fails verification).

     >>> from cxmanage_api.cx_exceptions import InvalidImageError

    :param msg: Exceptions message and details to return to the user.
    :type msg: string
    :raised: When an image is not valid. (i.e. fails verification).

    """

    def __init__(self, msg):
        """Default constructor for the InvalidImageError class."""
        super(InvalidImageError, self).__init__()
        self.msg = msg

    def __str__(self):
        """String representation of this Exception class."""
        return self.msg


class NoBootCmdDefaultError(Exception):
    """Raised when there is no bootcmd_default arg in the boot order.

     >>> from cxmanage_api.cx_exceptions import NoBootCmdDefaultError

    :param msg: Exceptions message and details to return to the user.
    :type msg: string
    :raised: When there is no bootcmd_default arg in the boot order.

    """

    def __init__(self, msg):
        """Default constructor for the NoBootCmdDefaultError class."""
        super(NoBootCmdDefaultError, self).__init__()
        self.msg = msg

    def __str__(self):
        """String representation of this Exception class."""
        return self.msg


class UnknownBootCmdError(Exception):
    """Raised when the boot command is not: run bootcmd_pxe, run bootcmd_sata,
       run bootcmd_mmc, setenv bootdevice, or reset.

     >>> from cxmanage_api.cx_exceptions import UnknownBootCmdError

    :param msg: Exceptions message and details to return to the user.
    :type msg: string
    :raised: When the boot command is not: run bootcmd_pxe, run bootcmd_sata,
             run bootcmd_mmc, setenv bootdevice, or reset.

    """

    def __init__(self, msg):
        """Default constructor for the UnknownBootCmdError class."""
        super(UnknownBootCmdError, self).__init__()
        self.msg = msg

    def __str__(self):
        """String representation of this Exception class."""
        return self.msg


class CommandFailedError(Exception):
    """Raised when a command has failed.

     >>> from cxmanage_api.cx_exceptions import CommandFailedError

    :param results: Command results. (map of nodes->results)
    :type results: dictionary
    :param errors: Command errors. (map of nodes->errors)
    :type errors: dictionary
    :raised: When a command has failed.

    """

    def __init__(self, results, errors):
        """Default constructor for the CommandFailedError class."""
        self.results = results
        self.errors = errors

    def __str__(self):
        """String representation of this Exception class."""
        return 'Results: %s Errors: %s' % (self.results, self.errors)


# End of file: exceptions.py

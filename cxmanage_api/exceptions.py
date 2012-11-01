"""Defines the custom exceptions used by the cxmanage_api project."""


class TimeoutError(Exception):
    """Raised when a timeout has been reached."""
    
    def __inti__(self, msg):
        """Default constructor for the TimoutError class.
        
        :param msg: Exceptions message and details to return to the user.
        :type msg: string
        """
        super(TimeoutError, self).__init__()
        self.msg = msg
    
    def __str__(self):
        """String representation of this Exception class."""
        return self.msg


class NoPartitionError(Exception):
    """Raised when a partition is not found."""
    
    def _init__(self, msg):
        """Default constructor for the NoPartitionError class."""
        super(NoPartitionError, self).__init__()
        self.msg = msg
        
    def __str__(self):
        """String representation of this Exception class."""
        return self.msg
    
     
# End of file: exceptions.py
 
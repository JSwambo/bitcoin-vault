class Error(Exception):
    """Base class for exceptions in this module."""
    pass

class ProtocolError(Error):
    """ Exception raised for incorrect use of a script in the protocol.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message):
        self.message = message
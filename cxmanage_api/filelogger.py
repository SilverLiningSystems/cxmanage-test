#!/usr/bin/env/python

# Copyright 2013 Calxeda, Inc. All Rights Reserved.


import os


class FileLogger:
    """Simple class that logs messages to a file."""

    def __init__(self, filename=None):
        if filename:
            self.file = open(filename, "w")
        else:
            self.file = None

    def log(self, message, add_newlines=True):
        """Write message to the log file. If message is a list of strings,
        newline characters will be added between items unless add_newlines
        is set to False.

        :param message: Text to write to the files
        :type message: string or list of strings
        :param add_newlines: Whether to add newline characters before
        every item in message if message is a list of strings.
        :type add_newlines: bool

        """
        if add_newlines:
            if type(message) == str:
                self.file.write("\n" + message)
            else:
                # join() doesn't add a newline before the first item
                message[0] = "\n" + message[0]
                self.file.write("\n".join(message))
        else:
            if type(message) == str:
                self.file.write(message)
            else:
                self.file.write("".join(message))

        # Make sure we actually write to disk
        self.file.flush()
        os.fsync(self.file.fileno())

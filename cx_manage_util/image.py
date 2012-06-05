#!/bin/env python

class Image:
    """ An image consists of an image type and a filename """

    def __init__(self, image_type, filename):
        self.type = image_type
        self.filename = filename

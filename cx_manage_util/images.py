#!/bin/env python

""" The images class is a collection of Calxeda firmware images.  FIXME:
fill in the rest of the description.  We'll probably make the location
a URI. """

import os

class Images:
    def __init__(self):
        self._images = {} # this will be a dictionary of tag: image object

    def add_image(self, image, image_type, filename):
        # TODO: validate properly
        if os.path.exists(filename):
            self._images[image] = Image(image_type, filename)
        else:
            raise ValueError

    def get_image_type(self, image):
        return self._images[image].get_type()

    def get_image_filename(self, image):
        return self._images[image].get_filename()

class Image:
    def __init__(self, image_type, filename):
        self._type = image_type
        self._filename = filename

    def get_type(self):
        return self._type

    def get_filename(self):
        return self._filename

#!/bin/env python

""" The images class is a collection of Calxeda firmware images. """

import os

class Images:
    """ Contains a collection of known images """

    def __init__(self):
        self._images = {} # this will be a dictionary of tag: image object

    def add_image(self, image_name, image_type, filename):
        """ Add an image to this collection """

        # TODO: validate properly
        if os.path.exists(filename):
            self._images[image_name] = Image(image_type, filename)
        else:
            raise ValueError

    def get_image_type(self, image_name):
        """ Return the image type associated with this name """
        return self._images[image_name].get_type()

    def get_image_filename(self, image_name):
        """ Return the image filename associated with this name """
        return self._images[image_name].get_filename()

class Image:
    """ An image consists of an image type and a filename """

    def __init__(self, image_type, filename):
        self._type = image_type
        self._filename = filename

    def get_type(self):
        """ Return the type of this image """
        return self._type

    def get_filename(self):
        """ Return the filename of this image """
        return self._filename

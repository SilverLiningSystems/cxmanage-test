#!/bin/env python

""" The images class is a collection of Calxeda firmware images.  FIXME:
fill in the rest of the description.  We'll probably make the location
a URI. """

class Images:
    def __init__(self):
        self._images = {} # this will be a dictionary of tag: image object

    def get_settings_str(self):
        # FIXME
        return "No settings."

    def add_image(self, image, image_type, filename):
        self._images[image] = Image(image_type, filename)

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

#!/bin/env python

""" The images class is a collection of Calxeda firmware images.  FIXME:
fill in the rest of the description.  We'll probably make the location
a URI. """

class images:
    def __init__(self):
        self._images = {} # this will be a dictionary of tag: image object
        self._location = "http://127.0.0.1"

    def get_settings_str(self):
        # FIXME
        return "No settings."

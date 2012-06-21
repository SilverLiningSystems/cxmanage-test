#Copyright 2012 Calxeda, Inc.  All rights reserved.

from pkgutil import iter_modules

prefix = __name__ + "."
plugins = [__import__(x[1], fromlist="dummy")
        for x in iter_modules(__path__, prefix)]

def add_args(p):
    for plugin in plugins:
        plugin.add_args(p)

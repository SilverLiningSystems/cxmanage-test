# Copyright (c) 2012, Calxeda Inc.
#
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
# * Redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer.
# * Redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution.
# * Neither the name of Calxeda Inc. nor the names of its contributors
# may be used to endorse or promote products derived from this software
# without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT HOLDERS OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS
# OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR
# TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF
# THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH
# DAMAGE.
"""Generates .rst files for all .py files specified in the sources.

:author: Eric Vasquez
:contact: eric.vasquez@calxeda.com
:copyright: (c) 2012, Calxeda Inc.

"""

import os
import sys


SRC_FILES = {# Package
             'cxmanage_api' :
             {
             # Python src file  : rst doc title
             'command'          : 'Command',
             'crc32'            : 'CRC32',
             'cx_exceptions'    : 'Cxmanage Exceptions',
             'fabric'           : 'Fabric',
             'firmware_package' : 'Firmware Package',
             'image'            : 'Image',
             'infodump'         : 'Info Dump',
             'node'             : 'Node',
             'simg'             : 'SIMG',
             'tftp'             : 'TFTP',
             'ubootenv'         : 'U-Boot Environment'
             }
            }
SRC_DIR = os.path.dirname(os.path.abspath('.'))
RST_DIR = os.path.dirname(os.path.abspath(__file__))
BLACKLIST = []


def parse_source(src_file):
    """Parses a given source file to get class and function names.
    
    :param src_file: A file path. (abspath)
    :type src_file: string
    :return: a dictionary mapping class to methods and a list of functions
    :rtype: dictionary
    """
    def _get_object_name(line):
        """Takes a class, function or method declaration and get the name."""
        name = line.split()[1].split('(')[0].strip()
        return name.rstrip(':')

    #
    # Parse Source
    #
    classes, functions = {}, []
    with open(src_file, 'r') as file_:
        class_ = None
        lines = file_.readlines()        
        
        for line in lines:
            if (line.startswith('class ')):
                name = _get_object_name(line)
                class_ = name
                classes[name] = []
            elif (line.startswith('    def ') and line.count('(')):
                if (class_):
                    name = _get_object_name(line)
                    if (not name.startswith('_')):
                        classes[class_].append(name)
            elif (line.startswith('def ') and line.count('(')):
                functions.append(_get_object_name(line))
    
    for class_name, function_names in classes.items():
        classes[class_name] = sorted(function_names)
    return classes, functions
            
def main():
    """Entry point for this script ..."""
    for package, module in SRC_FILES.items():
        for module_name, module_title in module.items():
            doc = os.path.join(RST_DIR, '%s.rst' % module_name)
            with open('%s' % doc, 'w') as rst_file:
                py_src = os.path.join(SRC_DIR, '%s.py' % module_name)
                classes, functions = parse_source(py_src)
                rst_file.write(module_title + '\n')
                rst_file.write('_' * len(module_title) + '\n\n')
                
                if (len(functions) > 0):
                    rst_file.write('.. currentmodule:: %s.%s\n\n' % 
                                   (package, module_name))
                    rst_file.write('.. autosummary::\n')
                    rst_file.write('    :nosignatures:\n\n')
                    for func in functions:
                        rst_file.write('    %s\n' % func)
                    rst_file.write('\n')
                
                if (classes != {}):
                    rst_file.write('.. currentmodule:: %s.%s\n\n' % 
                                   (package, module_name))
                    rst_file.write('.. autosummary::\n')
                    rst_file.write('    :nosignatures:\n\n')
                    for class_name in classes.keys():
                        rst_file.write('    %s\n' % class_name)
                    rst_file.write('\n')
                    for class_name, function_list in classes.items():
                        if (len(function_list) > 0):
                            rst_file.write('    .. automethod::\n')
                            for function_name in function_list:
                                rst_file.write('        %s.%s\n' % 
                                               (class_name, function_name))
                        rst_file.write('\n\n')
                
                for func in functions:
                    rst_file.write('.. autofunction:: %s\n' % func)
                
                for class_name in classes.keys():
                    rst_file.write('.. autoclass:: %s\n' % class_name)
                    rst_file.write('    :members:\n')
                    if (module_name not in BLACKLIST):
                        rst_file.write('    :inherited-members:\n')
                    rst_file.write('    :show-inheritance:\n')
                    rst_file.write('\n')
   

if __name__ == '__main__':
    sys.exit(main())


# End of file: ./docs/generate_api_rst.py

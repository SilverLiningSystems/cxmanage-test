"""Generates .rst files for .py files encountered in the SRC_DIR

:author: Eric Vasquez
:contact: eric.vasquez@calxeda.com
:copyright: (c) 2012, Calxeda Inc.

"""

import os
import sys


SRC_FILES = {}
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
        classes[class_name] = sorted(list(set(function_names)))
    return classes, sorted(list(set(functions)))


def main():
    """Entry point for this script."""
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


# Go!
if __name__ == '__main__':
    sys.exit(main())


# End of file: ./docs/generate_api_rst.py

Firmware Installation Basics
----------------------------

Overview
========

Now that we can construct a Fabric object using the Cxmanage API, we can use the
Fabric functionality to load firmware onto each node.

.. note::
    * This tutorial assumes:
        * Basic Object Oriented Programming knowledge
        * Basic Python language syntax and data structures

Example
=======

**Lets start by stating what the end goals of this example will be:**
    1. Construct a FirmwarePackage object using the Cxmanage API.
    #. Construct a Fabric object using the Cxmanage API.
    #. Print out each Nodes' current firmware version.
    #. If the Fabric is *updatable*, update the firmware.
    #. If the Fabric is not, print out which Node(s) cannot be updated.

.. seealso::
    Fabric `is_updatabale() <fabric.html#cxmanage_api.fabric.Fabric.is_updatable>`_ for more details on the functions we'll be using.

**Now lets dive right in with code ...**

You can either write a script in your favorite text editor of choice or use
Python's Interactive Interpreter. The interactive interpreter is used for these
code examples, however ANY of this code can be copied/pasted into a script.

To start the Interactive Interpreter, at a terminal command-line prompt::

   python
    Python 2.7.3 (default, Aug  1 2012, 05:14:39)
    [GCC 4.6.3] on linux2
    Type "help", "copyright", "credits" or "license" for more information.
   >>>

.. note::
    * If you're using a Virtual Environment ... BEFORE you start the interpreter, be sure to:
        workon <VirtualEnvironment Name>

.. seealso:: `Using the Python Interpreter <http://docs.python.org/2/tutorial/interpreter.html>`_


The Code
########

.. code-block:: python
    :linenos:

    from cxmanage_api.firmware_package import FirmwarePackage
    fw_pkg = FirmwarePackage('ECX-1000_update-v1.6.1-2-g279e340.tar.gz')

    from cxmanage_api.fabric import Fabric
    my_fabric = Fabric('10.20.1.9')

    basic_info = my_fabric.info_basic()
    for node_num, info in basic_info.items():
        print 'Node %d Firmware Version: %s' % (node_num, info.version)

    results = my_fabric.is_updatable(package=fw_pkg)
    if (False in results.values()):
        print 'The following nodes CANNOT be updated:'
        print '%s' % [node for node, value in results.items() if value is False]
    else:
        print 'Fabric Firmware Update -> %s' % fw_pkg.version
        my_fabric.update_firmware(package=fw_pkg)

    new_basic_info = my_fabric.info_basic()
    for node_num, info in new_basic_info.items():
        print 'Node %d Firmware Version: %s' % (node_num, info.version)


The Output
##########

::
    Foo Bar Baz

Line by Line Explaination
#########################


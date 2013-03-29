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
    #
    # This needs to be the absolute path to the Firmware Package
    #
    fw_pkg = FirmwarePackage(filename='ECX-1000_update-v1.6.1-2-g279e340.tar.gz')

    from cxmanage_api.fabric import Fabric
    my_fabric = Fabric('10.20.1.9')        
    versions = my_fabric.get_versions_dict()

    for node_number, version in versions.items():
        for key, value in version.items():
            if ('firmware' in key):
                print 'Node %d: FW Version: %s' % (node_number, value)

    results = my_fabric.is_updatable(package=fw_pkg)
    if (False in results.values()):
        print 'The following nodes CANNOT be updated:'
        print '%s' % [node for node, value in results.items() if value is False]
    else:
        print 'Fabric Firmware Update -> %s' % fw_pkg.version
        print '=' * 80
        my_fabric.update_firmware(package=fw_pkg)

    new_basic_info = my_fabric.get_versions_dict()
    for node_number, version in versions.items():
        for key, value in version.items():
            if ('firmware' in key):
                print 'Node %d: FW Version: %s' % (node_number, value)

Again, in about 10 lines of (useful) code, we are able to upgrade a Fabric or
even multiple Fabrics using the Cxmanage API.

The Output
##########

::

    Node 0: FW Version: ECX-1000-v2.0.0-0
    Node 1: FW Version: ECX-1000-v2.0.0-0
    Node 2: FW Version: ECX-1000-v2.0.0-0
    Node 3: FW Version: ECX-1000-v2.0.0-0
    ================================================================================
    Fabric Firmware Update -> ECX-1000-v2.1.1-1
    ================================================================================
    Node 0: FW Version: ECX-1000-v2.1.1-1
    Node 1: FW Version: ECX-1000-v2.1.1-1
    Node 2: FW Version: ECX-1000-v2.1.1-1
    Node 3: FW Version: ECX-1000-v2.1.1-1

Line by Line Explaination
#########################

*Line 1:* Imports the FirmwarePackage class from the `installed <index.html#installation>`_ cxmanage_api.

.. code-block:: python

    from cxmanage_api.firmware_package import FirmwarePackage

*Line 5:* Creates a firmware package object that we'll use for updating.

.. code-block:: python

    fw_pkg = FirmwarePackage('ECX-1000_update-v1.6.1-2-g279e340.tar.gz')

.. note::
    * Requires a VALID Firmware Package image.

*Line 7:* Imports the Fabric class from the cxmanage_api.

.. code-block:: python

    from cxmanage_api.fabric import Fabric

*Line 8:* Creates the actual Fabric we'll be working with.

.. code-block:: python

    my_fabric = Fabric('10.20.1.9')

*Line 9:* Gets the Hardware/Software versions dictionary from the Fabric.

.. code-block:: python

    versions = my_fabric.get_versions_dict()

*Lines 11-14:* A **for** loop that iterates over the **versions** dictionary
and prints the Nodes firmware version (ONLY).

.. code-block:: python

    for node_number, version in versions.items():
        for key, value in version.items():
            if ('firmware' in key):
                print 'Node %d: FW Version: %s' % (node_number, value)

*Line 16:* Is a VERY important line of code. It asks every Node on the Fabric
if it can be updated to the proposed Firmware Package. It returns a dictionary
of {node_number : True/False} stating whether or not an update is possible. We
store that dictionary in **results**.

.. code-block:: python

    results = my_fabric.is_updatable(package=fw_pkg)

*Lines 17-18:* Tests to see if False occurs for ANY Node by simply looking at
the *values* in the dictionary. If False occurs, we'll figure out which Node(s)
are offending.

*Line 18:* Is the list comprehension that returns a list of all offending Nodes.

.. code-block:: python

    if (False in results.values()):
        print 'The following nodes CANNOT be updated:'
        print '%s' % [node for node, value in results.items() if value is False]

*Lines 17-22:* Are the upgrade code. If all Nodes can be updated, we do so
in this block of code.

.. code-block:: python

    else:
        print 'Fabric Firmware Update -> %s' % fw_pkg.version
        print '=' * 80
        my_fabric.update_firmware(package=fw_pkg)

*Lines 24-26:* Do essentially what lines 11-14 did ... Gets versions_dict from each
Node on the Fabric and prints it out. Duplicate code like this should be factored
into a function call.

.. code-block:: python

    new_basic_info = my_fabric.get_versions_dict()
    for node_number, version in versions.items():
        for key, value in version.items():
            if ('firmware' in key):
                print 'Node %d: FW Version: %s' % (node_number, value)


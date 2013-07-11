=================================
Cxmanage Python API Documentation
=================================

The Cxmanage Python API provides a way for client code to access a Calxeda
System on a Chip (SoC).

The Cxmanage Python API focuses on the connectivity between the issuing client
and the Baseboard Management Controller (BMC) by using a Python IPMI interface.

Features
========
This Python API provides a mechanism for (at a high level):
    * Creating Nodes (single SoC objects)
    * Creating Fabrics (a group of Nodes, controlled by Node 0)
    * Utility functions to:
        * install firmware
        * reset to defaults (mc reset, factory defaults)
        * send commands (and get repsonses) to Nodes or Fabrics
        * get/set the boot order
        * get/set the power policy
        * much more ...

Installation
============

Requirements
------------
``Operating Systems``
   **Ubuntu** 12.04 LTS (or greater)

   **Windows** 7 (or greater)

``Python``
    Python version 2.6

.. note::
    * Windows requires `Cygwin <http://cygwin.com>`_
    * For Cygwin compatibility, Python version 2.6 is adhered to.

Installation Steps
------------------
``Linux``
    `Calxeda Linux Official Install Instructions <https://wiki.calxeda.com/display/DOCSUG/Installing+cxmanage+%28Linux%29>`_

``Windows``
    `Calxeda Windows Official Install Instructions <https://wiki.calxeda.com/display/DOCSUG/Installing+cxmanage+and+IPMItool+%28Windows%29>`_

Usage
=====
API Quick Start Guide
---------------------
Once properly installed, using the API is fairly trivial. As long as the
cxmanage_api library is in your PYTHONPATH (or in the virtual enviroment
PYTHONPATH) you can simply declare and use Calxeda objects.

The following is just a small excerpt of how to use the Cxmanage Python API.
More extensive examples and sample code can be found in the development
tutorials and Getting Started guide.


.. note::
    * If you're using a Virtual Environment, be sure to:
        workon <VirtualEnvironment Name>


Example code::

    #
    # Import the essentials!
    #
    from cxmanage_api.node import Node
    from cxmanage_api.fabric import Fabric
    #
    # A list of some Node capabilities
    #
    for i in [x for x in dir(Node) if not x.startswith('_')]: print i
    ...
    config_reset
    get_boot_order
    get_fabric_ipinfo
    get_fabric_macaddrs
    get_firmware_info
    get_firmware_info_dict
    get_mac_addresses
    get_power
    get_power_policy
    get_sensors
    get_sensors_dict
    get_server_ip
    get_ubootenv
    get_versions
    get_versions_dict
    ipmitool_command
    is_updatable
    mc_reset
    set_boot_order
    set_power
    set_power_policy
    tftp_address
    update_firmware


    #
    # The easiest way to create a Node is to just give the ip address to the
    # constructor ... But there are other parameters that can be set ...
    #
    my_node = Node('10.20.1.9')

    #
    # Get the Node's MAC Addresses
    #
    my_node.get_macaddrs()
    ['fc:2f:40:3b:ec:40', 'fc:2f:40:3b:ec:41', 'fc:2f:40:3b:ec:42']

    #
    # Define a Fabric by simply using an ip address of ANY Node on that Fabric.
    #
    my_fabric = Fabric(ip_address=my_node.ip_address)

    #
    # Get the MAC Addresses of ALL the nodes on the Fabric ...
    #
    my_fabric.get_macaddrs()

    #
    # Output
    #
    {0 : ['fc:2f:40:3b:ec:40',
          'fc:2f:40:3b:ec:41',
          'fc:2f:40:3b:ec:42'],
     1 : ['fc:2f:00:00:00:00',
          'fc:2f:40:91:dc:41',
          'fc:2f:40:91:dc:42'],
     2 : ['fc:2f:40:ab:f7:14',
          'fc:2f:40:ab:f7:15',
          'fc:2f:40:ab:f7:16'],
     3 : ['fc:2f:40:88:b3:6c',
          'fc:2f:40:88:b3:6d',
          'fc:2f:40:88:b3:6e']}

    #
    # Fabric objects have the same function identities as Nodes. Fabrics simply
    # facilitate Node functions to many Nodes in a multi-threaded fashion.
    #

Getting Started
===============
So you have the Cxmanage Python API properly installed, so now what?

The Cxmanage Python API Docs will give you information on how to use Calxeda
classes and functions.

You can view the API source for even more clarity on the internals. Or jump
right into the Code Examples.

API Docs & Code Examples
------------------------

``API Documentation``

.. toctree::

    Node <node>
    Fabric <fabric>
    Tasks <tasks>
    CRC32 <crc32>
    Cxmanage API Exceptions <cx_exceptions>
    Firmware Package <firmware_package>
    Image <image>
    Internal/External TFTP <tftp>
    SIMG <simg>
    U-Boot Environment <ubootenv>
    IP Retriever <ip_retriever>
    Loggers <loggers>

``Code Examples``

.. toctree::

    Fabric Basics <fab_basics>
    Firmware Installation Basics <fw_install.rst>
    Index <contents>

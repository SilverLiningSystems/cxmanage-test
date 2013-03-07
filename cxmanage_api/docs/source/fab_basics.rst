Fabric Basics
-------------

Overview
========

Constructing a Fabric object in Python is **VERY** easy. You simply need to
know the ip address of *ANY* Node in your configuration ...
Thats it. The API will do the rest!

What purpose do Fabric objects in Python do for me as a user?

**At a glance, they're useful for:**
    * Performing the same action on one, all, or a subset of nodes.
    * Gathering real time information from the Fabric (statistics, topology,
      software versions, etc.)

.. note::
    * This tutorial assumes:
        * Basic Object Oriented Programming knowledge
        * Basic Python language syntax and data structures
    
Example
=======

**Lets start by stating what the end goals of this example will be:**
    1. Construct a Fabric object using the Cxmanage API.
    #. Query the Fabric object for **version** information from each node.
    #. Print out the information.

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

    from cxmanage_api.fabric import Fabric
    my_fabric = Fabric('10.20.1.9')               # 1. Construct a Fabric Object ...
    versions = my_fabric.get_versions_dict()      # 2. Get the versions info for each node ...
    
    for node_number, version in versions.items(): # 3. Print out the Information
        print 'SW/HW Version Info for Node %d:\n' % node_number
        for key, value in version.items():
            print('%s = %s' % (key, value))
    print('=' * 80)

Thats it! In less than 10 lines of code, we accomplished all of our stated goals with
the help of the Cxmanage API. Additionally, this code scales for Fabrics of N nodes.


The Output
##########

::

    SW/HW Version Info for Node 0:
    
    iana = 38605
    ubootenv_version = v2013.01-rc1_cx_2013.01.17-2-g3e
    ecme_version = v1.1.0-141-g8091aea
    hardware_version = EnergyCard X02
    cdb_version = v1.1.0-141-g8091aea
    ecme_timestamp = 1362686083
    bootlog_version = v1.1.0-141-g8091aea
    a9boot_version = v2012.12.21-5-gf0559d7
    stage2_version = v1.1.0-141-g8091aea
    dtb_version = v3.8-rc4-2-gc841f01
    firmware_version = ECX-1000-v2.1.1-1-g56b6358
    uboot_version = v2013.01-rc1_cx_2013.01.17-2-g3e
    ================================================================================
    SW/HW Version Info for Node 1:
    
    iana = 38605
    ubootenv_version = v2013.01-rc1_cx_2013.01.17-2-g3e
    ecme_version = v1.1.0-141-g8091aea
    hardware_version = EnergyCard X02
    cdb_version = v1.1.0-141-g8091aea
    ecme_timestamp = 1362686083
    bootlog_version = v1.1.0-141-g8091aea
    a9boot_version = v2012.12.21-5-gf0559d7
    stage2_version = v1.1.0-141-g8091aea
    dtb_version = v3.8-rc4-2-gc841f01
    firmware_version = ECX-1000-v2.1.1-1-g56b6358
    uboot_version = v2013.01-rc1_cx_2013.01.17-2-g3e
    ================================================================================
    SW/HW Version Info for Node 2:
    
    iana = 38605
    ubootenv_version = v2013.01-rc1_cx_2013.01.17-2-g3e
    ecme_version = v1.1.0-141-g8091aea
    hardware_version = EnergyCard X02
    cdb_version = v1.1.0-141-g8091aea
    ecme_timestamp = 1362686083
    bootlog_version = v1.1.0-141-g8091aea
    a9boot_version = v2012.12.21-5-gf0559d7
    stage2_version = v1.1.0-141-g8091aea
    dtb_version = v3.8-rc4-2-gc841f01
    firmware_version = ECX-1000-v2.1.1-1-g56b6358
    uboot_version = v2013.01-rc1_cx_2013.01.17-2-g3e
    ================================================================================
    SW/HW Version Info for Node 3:
    
    iana = 38605
    ubootenv_version = v2013.01-rc1_cx_2013.01.17-2-g3e
    ecme_version = v1.1.0-141-g8091aea
    hardware_version = EnergyCard X02
    cdb_version = v1.1.0-141-g8091aea
    ecme_timestamp = 1362686083
    bootlog_version = v1.1.0-141-g8091aea
    a9boot_version = v2012.12.21-5-gf0559d7
    stage2_version = v1.1.0-141-g8091aea
    dtb_version = v3.8-rc4-2-gc841f01
    firmware_version = ECX-1000-v2.1.1-1-g56b6358
    uboot_version = v2013.01-rc1_cx_2013.01.17-2-g3e
    ================================================================================

Line by Line Explaination
#########################

*Line 1:* Imports the Fabric class from the `installed <index.html#installation>`_ cxmanage_api.

.. code-block:: python

    from cxmanage_api.fabric import Fabric

*Line 2:* Accomplished our first goal by creating the Fabric object with an ip
address we knew about.

.. code-block:: python

    my_fabric = Fabric('10.20.1.9')

*Line 3:* Accomplished our second goal by simply asking the Fabric for Node 
version info and storing the result in the 'versions' variable, which is a 
dictionary in the format: {node_number : {version: info}}. 

.. code-block:: python

    versions = my_fabric.get_versions_dict()

*Line 4:* Is blank ... it does nothing but serves the purpose of nice code format.

*Line 5:* Is a **for** loop that is going to iterate over the **versions**
dictionary of result objects and store the keys to the dictionary in variable:
**node_number**, as well as store the values for each key in the variable **version**.

.. code-block:: python

    for node_number, version in versions.items():

*Line 6:* The first of a couple of print statements (*Goal #3*). Its going to
print some text but most notably, its going to do this on every iteration of the
**for** loop and filling in **node_number** for every %d. The \\n is just a new-line
character.

.. code-block:: python

    print 'SW/HW Version Info for Node %d:\n' % node_number

*Line 7:* Starts another **for** loop that will get each version attribute, and
its value and assign them to the variables 'key' and 'value'. We do this so we 
can print out each different HW/SW version.

.. code-block:: python

    for key, value in version.items():

*Line 8:* Prints the key and its value for the version.

.. code-block:: python

    print('%s = %s' % (key, value))

*Line 9:* Prints the character '=' 80 times.

.. code-block:: python

    print('=' * 80)

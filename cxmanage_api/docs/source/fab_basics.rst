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
    #. Query the Fabric object for **basic** information from each node.
    #. Print out the information.

.. seealso:: `Fabric Info Basic <fabric.html#cxmanage_api.fabric.Fabric.info_basic>`_ & `Node Info Basic <node.html#cxmanage_api.node.Node.info_basic>`_ for more details on the function(s) we'll be using.

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
    my_fabric = Fabric('10.20.1.9')                 # 1. Construct a Fabric Object ...
    basic_info = my_fabric.info_basic()             # 2. Get basic information from each node

    for node_number, info in basic_info.items():    # 3. Print out the Information
        print 'Basic Info for Node %d:\n' % node_number
        versions = [name for name in dir(info) if not name.startswith('_')]
        for version in versions:
            print '%s = %s' % (version, getattr(info, version))
        print '=' * 80

Thats it! In just 10 lines of code, we accomplished all of our stated goals with
the help of the Cxmanage API. Additionally, this code scales for Fabrics of N nodes.


The Output
##########

::

    Basic Info for Node 0:

    a9boot_version = v2012.10.16
    bootlog_version = v0.9.1-39-g7e10987
    build_number = 7E10987C
    card = EnergyCard X02
    cdb_version = v0.9.1-39-g7e10987
    dtb_version = v3.6-rc1_cx_2012.10.02
    header = Calxeda SoC (0x0096CD)
    soc_version = v0.9.1
    stage2_version = v0.9.1-39-g7e10987
    timestamp = 1352911670
    uboot_version = v2012.07_cx_2012.10.29-6-g6605d9
    ubootenv_version = v2012.07_cx_2012.10.29-6-g6605d9
    version = ECX-1000-v1.7.1-dirty
    ================================================================================
    Basic Info for Node 1:

    a9boot_version = v2012.10.16
    bootlog_version = v0.9.1-39-g7e10987
    build_number = 7E10987C
    card = EnergyCard X02
    cdb_version = v0.9.1-39-g7e10987
    dtb_version = v3.6-rc1_cx_2012.10.02
    header = Calxeda SoC (0x0096CD)
    soc_version = v0.9.1
    stage2_version = v0.9.1-39-g7e10987
    timestamp = 1352911670
    uboot_version = v2012.07_cx_2012.10.29-6-g6605d9
    ubootenv_version = v2012.07_cx_2012.10.29-6-g6605d9
    version = ECX-1000-v1.7.1-dirty
    ================================================================================
    Basic Info for Node 2:

    a9boot_version = v2012.10.16
    bootlog_version = v0.9.1-39-g7e10987
    build_number = 7E10987C
    card = EnergyCard X02
    cdb_version = v0.9.1-39-g7e10987
    dtb_version = v3.6-rc1_cx_2012.10.02
    header = Calxeda SoC (0x0096CD)
    soc_version = v0.9.1
    stage2_version = v0.9.1-39-g7e10987
    timestamp = 1352911670
    uboot_version = v2012.07_cx_2012.10.29-6-g6605d9
    ubootenv_version = v2012.07_cx_2012.10.29-6-g6605d9
    version = ECX-1000-v1.7.1-dirty
    ================================================================================
    Basic Info for Node 3:

    a9boot_version = v2012.10.16
    bootlog_version = v0.9.1-39-g7e10987
    build_number = 7E10987C
    card = EnergyCard X02
    cdb_version = v0.9.1-39-g7e10987
    dtb_version = v3.6-rc1_cx_2012.10.02
    header = Calxeda SoC (0x0096CD)
    soc_version = v0.9.1
    stage2_version = v0.9.1-39-g7e10987
    timestamp = 1352911670
    uboot_version = v2012.07_cx_2012.10.29-6-g6605d9
    ubootenv_version = v2012.07_cx_2012.10.29-6-g6605d9
    version = ECX-1000-v1.7.1-dirty
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

*Line 3:* Accomplished our second goal by simply asking the Fabric for Node info
and storing the result in the 'basic_info' variable, which is a dictionary in
the format: { node_number : info_basic_result_object }. We'll have to inspect
this object in a bit ...

.. code-block:: python

    basic_info = my_fabric.info_basic()

*Line 4:* Is blank ... it does nothing but serves the purpose of nice code format.

*Line 5:* Is a **for** loop that is going to iterate over the **basic_info**
dictionary of result objects and store the keys to the dictionary in variable:
**node_number**, as well as store the values for each key in the variable **info**.

.. code-block:: python

    for node_number, info in basic_info.items():

*Line 6:* The first of a couple of print statements (*Goal #3*). Its going to
print some text but most notably, its going to do this on every iteration of the
**for** loop and filling in **node_number** for every %d. The \\n is just a new-line
character.

.. code-block:: python

    print 'Basic Info for Node %d:\n' % node_number

*Line 7:* Because the basic_info contains result *objects*, we need to inspect
that object for the attributes.

Attributes are members of the result object's
class. In Python, they are accessed like this: object\ **.**\ attribute *[object<dot>attribute]*

We're going to use what's called a `list comprehension <http://docs.python.org/2/tutorial/datastructures.html#list-comprehensions>`_
to create a list new list of all of the attributes in the result object by using
the built in function `dir <http://docs.python.org/2/library/functions.html#dir>`_.
Because everything in Python is an object by default, they all have naturally
inherited attributes that we're not interested in. Python, by convention, uses
'__' and '_' preceeding attribute names for such things ... so we exclude those
from our list. All the attributes that meet our criteria get stored in **versions**.

.. code-block:: python

    versions = [name for name in dir(info) if not name.startswith('_')]

*Line 8:* Now that we have a list of information from the result object that we
are interested in printing *(versions)*, we simply begin to iterate over that list.

.. code-block:: python

    for version in versions:

*Line 9:* Prints the version (string name of the attribute) and the value that is
stored in the result object by making a call to the built-in function
`getattr <http://docs.python.org/2/library/functions.html#getattr>`_

.. code-block:: python

    print '%s = %s' % (version, getattr(info, version))

*Line 10:* Prints the character '=' 80 times.

.. code-block:: python

    print '=' * 80


.. image:: https://travis-ci.org/yuuichi-fujioka/python-odlclient.svg?branch=master
    :target: https://travis-ci.org/yuuichi-fujioka/python-odlclient

OpenDaylight Client for Python
##############################

How To Use
==========

install
-------

pypi package:

.. code::

   pip install python-odlclient

source:

.. code::

   pip install git+https://github.com/yuuichi-fujioka/python-odlclient.git

Run Command
-----------

OpenDaylight Host, Port, User and Password are passed via Environment Variable. e.g.:

.. code::

   ODL_HOST=192.168.0.100 odl node list

Environment Vairable Names are:

======== ========================================================================================
Name     Description
======== ========================================================================================
ODL_HOST OpenDaylight Hostname(default: localhost)
ODL_PORT OpenDaylight API Port(default: 8181)
ODL_USER OpenDaylight API User Name(default admin)
ODL_PASS OpenDaylight API Password(default: password)
ODL_URL  Default Restconf API Path(default: http://${ODL_HOST}:${ODL_PORT}/restconf/operational/)
======== ========================================================================================

* List Nodes

.. code::

   odl node list

* List Tables

.. code::

   odl table list openflow:1111111111

* List Flows

.. code::

   odl flow list openflow:1111111111

* List Node Connectors

.. code::

   odl connector list openflow:1111111111

* Add Flow

.. code::

   odl flow create openflow:201106209703495 100 29 --dl-src 00:00:00:00:00:00/01:00:00:00:00:00 --instructions output:1,output:2

If you want to know HTTP Request/Response details, you may set --debug and --verbose options. i.e.

.. code::

   odl --deubg --verbose node list

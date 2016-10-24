=================
Cabling and Patch
=================

The cabling and patch system is NAV is intended to give you information about to
which wall socket a switch port is physically patched. This may be useful for
instance to know which vlan a switch port should be configured to.

.. note:: Another way of doing this is to label your switch port with the jack
          it is connected to. This enables searching for the jack label in NAVs
          main search input.


Concepts
========

*Cabling* is where you register the cables that runs from your wall sockets to
the network room. They should have a jack label. *Patch* is where you register
which switch port the cable is connected to.

.. image:: cabling_and_patch.png


Cabling
=======

When adding cables, you must first choose the network room (Room in NAV) to
where the cable is connected. Then you enter the jack label. It helps to have
descriptive labels on your jacks.

If you want to you can add information about the cable for instance building and
office number.


Patch
=====

A patch is created from a switch port to an existing cable. First you choose
which switch you want to add the patch to. Based on this NAV knows what
(network) room that is relevant. When adding a patch to a switch port it will
list all unpatched cables in that room as patch candidates.


Port Details
============

If a switch port is patched using this system the cable information will be
displayed on the *Port details*-page in the *Connection* table.

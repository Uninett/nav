=========
PortAdmin
=========


Introduction
============

PortAdmin is a tool for configuring your switch ports by the help of a web
interface. It does so by communicating with a network device over SNMP [#f1]_.


What can PortAdmin do?
======================

Currently you can

* change port description
* change access vlan
* convert between trunk and access mode
* when an interface is a trunk you can change which vlans are tagged on the
  trunk.
* configure a voice vlan on an interface (:ref:`more_about_voice_vlan`)


What the interface tells you
============================

.. image:: portadmin-portlist.png

1. Port is the interface name given by the vendor. This is not possible to
   change
2. These indicators tells you the status of the interface:

  * *Enabled* indicates if the interface is enabled (green) or disabled (red)
  * *Linked* indicates if the interface has link (green) or not (red)

3. Port Description is the ifAlias. This is editable by the user. This is what
   you set by the *name* command on HP and *description* command on Cisco
   devices.
4. Vlan is the current active access vlan on the interface. You can change
   this by using the drop down menu. To set this interface to trunking mode,
   select the trunk option from the drop-down.
5. This interface is a trunk. To enter trunk edit mode, click the link.


How to use the interface
========================

Whenever you alter the values on an interface, the color of the row will
change. The save button will turn blue to indicate that you can use it to save
the changes.

.. image:: portadmin-change.png

When saving the changes a popup box will tell you what PortAdmin is doing and if
everything went well. As this process is best left uninterrupted, the button for
closing this popup will not display until everything is done.


Workflows
---------

I want to change the port description
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Start writing in the text field. The row and save button should change
color. Click save to save the changes.

I want to change the vlan
~~~~~~~~~~~~~~~~~~~~~~~~~

Choose vlan from the vlan drop down and click "Save". PortAdmin will disable the
interface for a few seconds and then enable it again. This is done to indicate
to any client connected to the interface that it should try to get a new
IP-address.

I want to edit a trunk
~~~~~~~~~~~~~~~~~~~~~~

Click the "Trunk" link. It will take you to the edit trunk interface. Make
your changes and click "Save changes".

I want to set an interface to trunking mode
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Click the vlan drop down and choose the "Trunk" option. The edit trunk
interface should appear. Set the native vlan and the tagged vlans. Click
"Save changes".

I want to set an interface to access mode
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Click the trunk link to edit the trunk. Remove all trunk vlans. Set the
native vlan to what you want the access vlan to be. Click "Save changes".

I want to save all changes without clicking all the save buttons
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Click one of the "Save all" buttons.

I want to activate the voice vlan on an interface
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If no column for activating voice vlans appear,
no voice vlans are configured in PortAdmins config file. This must be done
by a NAV administrator.

.. image:: portadmin-voicevlan.png

To activate the voice vlan, click the checkbox and click "Save".

I cannot edit an interface
~~~~~~~~~~~~~~~~~~~~~~~~~~

Two things can lead to an interface not being editable (no fields or drop downs appear):

- The admins of NAV have turned on vlan authorization. This means you can only
  edit interfaces that have a vlan that you are organizationally connected to.
- Something called a read-write community has not been set on the device. The
  read-write community is similar to a password and is needed for PortAdmin to
  be able to give commands to the device. To fix this, a NAV admin must edit the
  device in SeedDB and set the read-write community there. Also a read-write
  community must be set on the device itself.

Some parts of the interface is disabled/greyed out
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

See above.


The Config File
===============

PortAdmin has a config file. Some of the options that can be set in this file
are:

**voice_vlans**
    Voice vlans are the vlans you use for ip telephone traffic. If
    you define several vlans here, make sure only one of them is
    available on the netbox. Otherwise there is no way of knowing
    which one you want. If this option is set, the interface will
    display a checkbox to enable and disable voice vlan on the
    interface. :ref:`more_about_voice_vlan`

**cisco_voice_vlan**
    Cisco has its own terminology and configuration regarding voice vlans. NAV
    also supports this. To make NAV use Cisco Voice vlans, set this option to
    true. The default is false.

**vlan_auth**
    If you want to limit what users can do in PortAdmin you activate
    this option. What this does is limit the choice of vlans to the
    ones connected to the users organization.

**vlan and netident**
    Some network admins want to use a separate vlan to indicate that
    this interface does not route traffic. Use these options to define
    that vlan.  The vlan will be available for configuration for all
    users.

**format**
    Experimental feature. Makes you enforce a specific input format on
    the port description.


.. _more_about_voice_vlan:

More about the voice vlan
=========================

.. warning::
   The term *voice vlan* has two meanings in PortAdmin.

Originally what we meant by voice vlan was a vlan you as a network admin had
defined as *the vlan we use for voice traffic*. It was not related to the Cisco
or HP voice commands.

However since then PortAdmin has been extended to also support Cisco voice
vlans. This is not the default behaviour but is enabled in the config file. To
enable this you have to define voice vlans in the **voice_vlans directive** and tell
PortAdmin to use Cisco commands by enabling the **cisco_voice_vlan** directive.


.. rubric:: Footnotes

.. [#f1] Simple Network Management Protocol

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

3. Port Description is the ifAlias. This is editable by the user. This is
   what you set by the `name` command on HP and `description` command on Cisco
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

If the row flashes green after saving, that means the change went well. If a
red error message appears, this means there was an error making the change.


**I want to change the port description**

Start writing in the text field. The row and save button should change
color. Click save to save the changes.

**I want to change the vlan**

Choose vlan from the vlan drop down and click "Save". PortAdmin will disable the
interface for a few seconds and then enable it again. This is done to indicate
to any client connected to the interface that it should try to get a new
IP-address.

**I want to edit a trunk**

Click the "Trunk" link. It will take you to the edit trunk interface. Make
your changes and click "Save changes".

**I want to set an interface to trunking mode**

Click the vlan drop down and choose the "Trunk" option. The edit trunk
interface should appear. Set the native vlan and the tagged vlans. Click
"Save changes".

**I want to set an interface to access mode**

Click the trunk link to edit the trunk. Remove all trunk vlans. Set the
native vlan to what you want the access vlan to be. Click "Save changes".

**I want to save all changes without clicking all the save buttons**

Click one of the "Save all" buttons.

**I want to activate the voice vlan on an interface**

If no column for activating voice vlans appear,
no voice vlans are configured in PortAdmins config file. This must be done
by a NAV administrator.

.. image:: portadmin-voicevlan.png

To activate the voice vlan, click the checkbox and click "Save".

**I cannot edit an interface**

If an interface is not editable the admins of NAV have turned on vlan
authorization. This means you can only edit interfaces that have a
vlan that you are organizationally connected to.

**Some parts of the interface is disabled/greyed out**

See above.


The Config File
===============

PortAdmin has a config file. The options that can be set in this file are:

**voice_vlans**
    Voice vlans are the vlans you use for ip telephone traffic.  If
    you define several vlans here, make sure only one of them is
    available on the netbox. Otherwise there is no way of knowing
    which one you want. If this option is set, the interface will
    display a checkbox to enable and disable voice vlan on the
    interface. :ref:`more_about_voice_vlan`

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

The term `voice vlan` is misleading in PortAdmin. What we mean by voice vlan
is a vlan you as a network admin has defined as `the vlan we use for
voice traffic`. It is not related to the Cisco or HP voice commands.


.. rubric:: Footnotes

.. [#f1] Simple Network Management Protocol

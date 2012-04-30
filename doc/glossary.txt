.. _glossary:

========
Glossary
========

.. glossary::

    device
        A physical entity, which in most cases can be identified via a serial
        number.

    netbox
        A device which is reachable and can be monitored via an IP address.
        Also known as an IP device.

    IP device
        A device which is reachable and can be monitored via an IP address.
        Also known as a Netbox

    module
        A sub-entity of a Netbox, often replaceable in the form of a
        slot-insertable port or controller module, a transceiver, etc.  These
        are not normally addressable via a separate IP address, but are found
        by querying a Netbox using SNMP.  A module will be registered as a
        separate device in NAV, and tracked by serial number if available via
        SNMP.

========================================================
Adding support for a new environment probe device to NAV
========================================================

This guide will document an example of how to implement support for a new type
of environmental sensor probe in NAV.

The specific device used as an example is the AKCP sensorProbe8_, described by
the vendor as:

    A High-Speed, Accurate and Intelligent Monitoring device. The sensorProbe8 is
    a completely embedded host with a proprietary Linux like OS which includes
    TCP/IP stack, a built in web-server and full Email and SNMP functionality.

The goal
========

We have a sensorProbe8 device with a range of sensors connected (temperature,
humidity, etc.). We want each sensor value to be logged and graphed in NAV.

Sensors in NAV
==============

NAV has a :py:class:`nav.models.manage.Sensor` model, which maps arbitrary
sensors to Netboxes. This model describes how to collect data from a sensor
using SNMP, and NAV will automatically collect, log and graph data from all
Sensor instances registered in the database.

Conceptually, to add support for a new type of device with (possibly) multiple
sensors, you need to write a module that will discover the SNMP-available
sensors on this type of device and insert each of them into the NAV database.

In practice, you don't need to fiddle with the database at all, but just make
a class with a standard API to report a list of sensor descriptions to the
:program:`ipdevpoll` ``sensors`` plugin.

Course of action
================

1. We require AKCP's MIB definition. This can be downloaded from
   http://www.akcp.com/wp-content/uploads/2010/04/akcp_mib211210.zip
2. The MIB file must be converted to a Python file, using the
   :program:`smidump` program.
3. A MibRetriever class to detect and report the relevant sensors to NAV using
   this MIB must be written.
4. The :program:`ipdevpoll` ``sensors`` plugin must be configured to use the
   new MibRetriever class for the appropriate devices.

Dumping the MIB
===============

The downloaded :file:`akcp.mib` file defines a MIB module named
``SPAGENT-MIB``. Its definitions can be converted to a Python module thus:

.. code-block:: sh

   smidump -k -f python akcp.mib > python/nav/smidumps/SPAGENT-MIB.py

.. NOTE:: The SPAGENT-MIB definitions are somewhat flawed and will cause
   *smidump* to output some parsing errors. The ``-k`` command line option is
   there to make it produce its output despite many of these errors.

   It does not matter that the output file is invalid as a Python module
   name. It is loaded dynamically by NAV, and should be named verbatim after
   the MIB module it defines.

The :py:mod:`nav.smidumps` package is where NAV distributes Python versions of
the MIB definitions its code uses.

Examining the MIB
=================

Examining the MIB, reveals that it defines a number of tables; one for each
type of sensor that can be connected to a sensorProbe device. The table rows
typically define a sensor identifier, description, value readout, value unit
description and a bunch of other more or less interesting metadata.

What NAV needs in a Sensor record is:

* A unique identifier, that will not change when the sensor description
  changes.
* A description of the sensor.
* What base unit is used for the value readout.
* The precision of the value readout (SNMP doesn't support floating point
  numbers, so decimal precision is achieved by reporting a large integer and
  scaling it by a given factor).
* The exact OID to use in an SNMP GET operation to read the sensor value.

Hopefully, the MIB provides us with enough information to record all of this.
As an example, let's get some data about the available temperature sensors:

.. code-block:: console

   $ ls
   akcp.mib
   $ export MIBDIRS=/var/lib/mibs/ietf:.
   $ snmpwalk -v1 -c public 10.1.1.42 SPAGENT-MIB::sensorProbeTempTable
   SPAGENT-MIB::sensorProbeTempDescription.0 = STRING: "Ambient temperature"
   SPAGENT-MIB::sensorProbeTempDescription.1 = STRING: "Temperature2 Description"
   SPAGENT-MIB::sensorProbeTempDescription.2 = STRING: "Temperature3 Description"
   SPAGENT-MIB::sensorProbeTempDescription.3 = STRING: "Front of rack"
   SPAGENT-MIB::sensorProbeTempDescription.4 = STRING: "Back of rack"
   SPAGENT-MIB::sensorProbeTempDescription.5 = STRING: "Temperature6 Description"
   SPAGENT-MIB::sensorProbeTempDescription.6 = STRING: "Temperature7 Description"
   SPAGENT-MIB::sensorProbeTempDescription.7 = STRING: "Temperature8 Description"
   SPAGENT-MIB::sensorProbeTempDegree.0 = INTEGER: 22
   SPAGENT-MIB::sensorProbeTempDegree.1 = INTEGER: 0
   SPAGENT-MIB::sensorProbeTempDegree.2 = INTEGER: 0
   SPAGENT-MIB::sensorProbeTempDegree.3 = INTEGER: 17
   SPAGENT-MIB::sensorProbeTempDegree.4 = INTEGER: 16
   SPAGENT-MIB::sensorProbeTempDegree.5 = INTEGER: 0
   SPAGENT-MIB::sensorProbeTempDegree.6 = INTEGER: 0
   SPAGENT-MIB::sensorProbeTempDegree.7 = INTEGER: 0
   .
   .
   .
   SPAGENT-MIB::sensorProbeTempOnline.0 = INTEGER: online(1)
   SPAGENT-MIB::sensorProbeTempOnline.1 = INTEGER: offline(2)
   SPAGENT-MIB::sensorProbeTempOnline.2 = INTEGER: offline(2)
   SPAGENT-MIB::sensorProbeTempOnline.3 = INTEGER: online(1)
   SPAGENT-MIB::sensorProbeTempOnline.4 = INTEGER: online(1)
   SPAGENT-MIB::sensorProbeTempOnline.5 = INTEGER: offline(2)
   SPAGENT-MIB::sensorProbeTempOnline.6 = INTEGER: offline(2)
   SPAGENT-MIB::sensorProbeTempOnline.7 = INTEGER: offline(2)
   .
   .
   .
   SPAGENT-MIB::sensorProbeTempDegreeType.0 = INTEGER: celsius(1)
   SPAGENT-MIB::sensorProbeTempDegreeType.1 = INTEGER: fahr(0)
   SPAGENT-MIB::sensorProbeTempDegreeType.2 = INTEGER: fahr(0)
   SPAGENT-MIB::sensorProbeTempDegreeType.3 = INTEGER: celsius(1)
   SPAGENT-MIB::sensorProbeTempDegreeType.4 = INTEGER: celsius(1)
   SPAGENT-MIB::sensorProbeTempDegreeType.5 = INTEGER: fahr(0)
   SPAGENT-MIB::sensorProbeTempDegreeType.6 = INTEGER: fahr(0)
   SPAGENT-MIB::sensorProbeTempDegreeType.7 = INTEGER: fahr(0)
   SPAGENT-MIB::sensorProbeTempDegreeRaw.0 = INTEGER: 223
   SPAGENT-MIB::sensorProbeTempDegreeRaw.1 = INTEGER: 0
   SPAGENT-MIB::sensorProbeTempDegreeRaw.2 = INTEGER: 0
   SPAGENT-MIB::sensorProbeTempDegreeRaw.3 = INTEGER: 170
   SPAGENT-MIB::sensorProbeTempDegreeRaw.4 = INTEGER: 161
   SPAGENT-MIB::sensorProbeTempDegreeRaw.5 = INTEGER: 0
   SPAGENT-MIB::sensorProbeTempDegreeRaw.6 = INTEGER: 0
   SPAGENT-MIB::sensorProbeTempDegreeRaw.7 = INTEGER: 0
   .
   .
   .

From the MIB's description of the ``sensorProbeTempTable`` object, and from
this output, we can surmise the following:

* A total of 8 temperature sensors can be slotted in. All slots are reported
  in the table, but only the slots with an ``sensorProbeTempOnline`` value of
  ``online`` actually have an active temperature sensor connected.

* If we want decimal precision in our temperature readouts, we should use the
  ``sensorProbeTempDegreeRaw`` value. Unfortunately, the MIB definition says
  nothing about the exact resolution of this number, only that it is «higher»
  resolution than the ``sensorProbeTempDegree`` value. The *snmpwalk* output
  seems to suggest it provides a precision of a single decimal digit (i.e.
  divide the readout value by 10).

* The readout value unit is given by ``sensorProbeTempDegreeType`` (and we are
  given to suppose that a value of ``fahr`` means *degrees fahrenheit*).


Writing a MibRetriever
======================

NAV provides the :py:class:`nav.mibs.mibretriever.MibRetriever` base class,
which provides the basis for implementing classes with knowledge of specific
MIBs.

.. NOTE: MibRetrievers are not a particularly elegant implementation, as
   subclass implementations are isolated from each other, and there is no
   interface for querying arbitrary MIBs without first instantiating the
   specific MibRetriever subclasses you need.

First, we will need a class skeleton to start with. Create a
:file:`python/nav/mibs/spagent_mib.py` containing the following skeleton
code::

    from twisted.internet import defer
    from nav.mibs import reduce_index
    from nav.mibs.mibretriever import MibRetriever
    from nav.smidumps import get_mib


    class SPAgentMib(MibRetriever):
	mib = get_mib('SPAGENT-MIB')


The :program:`ipdevpoll` plugin :py:mod:`nav.ipdevpoll.plugins.sensors` needs
our MibRetriever to implement the ``get_all_sensors()`` method. This method
should return a Twisted_ Deferred_ - a «promise» of a future result. The
result must be a specific data structure describing a list of sensors
discovered on a device.


Example using a single hardcoded sensor
---------------------------------------

Let's hardcode an example result for a single temperature sensor, based on the
*snmpwalk* from above::

    class SPAgentMib(MibRetriever):
	mib = get_mib('SPAGENT-MIB')

	@defer.inlineCallbacks
	def get_all_sensors(self):
	    result = [
		{
		    'oid': '.1.3.6.1.4.1.3854.1.2.2.1.16.1.14.0',
		    'unit_of_measurement': 'celsius',
		    'precision': 1,
		    'scale': None,
		    'description': "Ambient temperature",
		    'name': "Ambient temperature",
		    'internal_name': "Ambient temperature",
		    'mib': 'SPAGENT-MIB',
		}
	    ]
	    return result

This returns a list of a single item: A dictionary describing the first
temperature sensor from the snmpwalk from above. The dictionary should contain
the following keys:


===================  =========================================================
Key                  Description
===================  =========================================================
oid                  The OID from which an SNMP-GET operation can extract the
                     readout value. In this example, it corresponds to
                     ``SPAGENT-MIB::sensorProbeTempDegreeRaw.0``
unit_of_measurement  The unit of measurement, used mostly for display
                     purposes. It may also be used to discover which sensors
                     actually measure temperature, when finding temperature
                     sensors for a room-view in NAV.
precision            The number of positions to move the decimal point of the
                     readout value. In this example, a readout value of *223*
                     will be registered as *22.3 degrees celsius*.
scale                The scale of the readout value. If the readout value was
                     specified as a number of *MegaWatts*, the base unit of
                     measurement would be *Watts* and the scale would be
                     *Mega*.
description          A (preferably) human-readable description of the sensor.
name                 A unique sensor name (can conceiveably be the same as the
                     description).
internal_name        An internal sensor name. If, for example, the actual
                     readout value OID for a specific sensor can change over
                     time, this should be an identifier that the sensor can be
                     recognized by over time. **This string is also used as
                     part of the Graphite metric name** when sensor readings
                     are sent to its Carbon backend.
mib                  Should be the name of the MIB module that the sensor
                     information was found in.
===================  =========================================================

A note on standardizing unit names
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Spelling and casing of unit names should be standardized throughout NAV. E.g.,
when a list of sensors is filtered to select only those that report
temperature values, it's much easier to write a filter if every temperature
sensor reports either ``celsius`` or ``fahrenheit``. If you register sensors
that have units like ``C``, ``F``, ``fahr``, ``°C`` or ``°F``, it's much
harder to find *all* the relevant sensors.

For this reason, an attempt has been made to standardize on a set of unit
names in the :class:`nav.models.manage.Sensor` model class. It would be wise
to import this model and use the relevant ``UNIT_*`` constants from this class
when returning sensor dicts.

This is exactly what we will do in the next example.


Collecting actual sensors from the MIB
--------------------------------------

Let's rewrite ``SPAgentMib`` to collect actual temperature sensors:

.. code-block:: python
   :linenos:
   :emphasize-lines: 9, 20

    from nav.models.manage import Sensor


    class SPAgentMib(MibRetriever):
	mib = get_mib('SPAGENT-MIB')

	@defer.inlineCallbacks
	def get_all_sensors(self):
	    result = yield self.retrieve_columns([
		'sensorProbeTempDescription',
		'sensorProbeTempOnline',
		'sensorProbeTempDegreeType',
	    ]).addCallback(self.translate_result).addCallback(reduce_index)

	    sensors = (self._temp_row_to_sensor(index, row)
		       for index, row in result.iteritems())

	    return [s for s in sensors if s]

	def _temp_row_to_sensor(self, index, row):
	    online = row.get('sensorProbeTempOnline', 'offline')
	    if online == 'offline':
		return

	    number = index[-1]
	    internal_name = 'temperature%s' % number
	    descr = row.get('sensorProbeTempDescription', internal_name)

	    mibobject = self.nodes.get('sensorProbeTempDegreeRaw')
	    readout_oid = str(mibobject.oid + str(index))

	    unit = row.get("sensorProbeTempDegreeType", None)
	    if unit == 'fahr':
		unit = Sensor.UNIT_FAHRENHEIT

	    return {
		'oid': readout_oid,
		'unit_of_measurement': unit,
		'precision': 1,
		'scale': None,
		'description': descr,
		'name': descr,
		'internal_name': internal_name,
		'mib': 'SPAGENT-MIB',
	    }

Lines 6 through 10 perform the actual SNMP query against a device. The
``get_all_sensors()`` method then delegates to the ``_temp_row_to_sensor()``
method the responsibility of translating each table row into a sensor
dictionary that can be used by the :program:`ipdevpoll` ``sensors`` plugin.

``_temp_row_to_sensors()`` takes the ``index`` and ``row`` arguments.
``index`` is the row index in the SNMP table (it is an OID suffix, in this
case a single-item tuple corresponding to the temperature sensor slot number).
``row`` is a dictionary containing the collected table columns, keyed by their
names.

Expanding these code examples to include all the sensor types provided by the
``SPAGENT-MIB`` is left as an excercise to the reader.


Have the sensors plugin use our new MibRetriever
------------------------------------------------

The ``sensors`` plugin employs the configuration sections ``sensors`` and
``sensors:vendormibs`` from :file:`ipdevpoll.conf` to decide which
MibRetriever classes to use for discovering sensors on a device. The plugins
decides on a list of MIBs to query based on the type of the device under query
(derived from the *enterprise number* in the device's ``sysObjectID`` value).

AKCP's enterprise number is 3854 (`as assigned by IANA
<http://www.iana.org/assignments/enterprise-numbers/enterprise-numbers>`_), so
we will use that to select our MibRetriever in the ipdevpoll config.

.. code-block:: ini

    [sensors:vendormibs]
    3854 = SPAgentMib

Alternatively, if you want a potentially more readable vendormibs section:

.. code-block:: ini

    [sensors:vendormibs]
    KCP_INC = SPAGENT-MIB

Both versions will work equally well. The latter works because
``VENDOR_ID_KCP_INC`` is a registered constant mapped to AKCP's enterprise
number in the :py:mod:`nav.enterprise.ids` module, and our ``SPAgentMib``
MibRetriever has been mapped to the ``SPAGENT-MIB`` module by importing the
smidump in its class definition.

If you implemented your MibRetriever outside of the NAV package tree, say in
the module :py:mod:`mynav.akcp`, you can modify the ``loadmodules`` option:

.. code-block:: ini

    [sensors]
    loadmodules = nav.mibs.* mynav.akcp


The ``sensors`` plugin runs as part of :program:`ipdevpoll`'s ``inventory``
job, normally every 6 hours. With these changes, adding an AKCP sensorProbe in
SeedDB will cause the ``sensors`` plugin to discover and insert the
temperature sensors of this device into NAV's database. The
:program:`ipdevpoll` ``1minstats`` job will retrieve the sensor readings once
every minute and send them to Graphite.

.. toctree::
    :hidden:

    /api/sensor
    /api/mibretriever

.. _sensorProbe8: https://www.akcp.com/akcp-products/sensorprobe-series/sensorprobe8/
.. _Twisted: https://twistedmatrix.com/
.. _Deferred: http://twistedmatrix.com/documents/current/api/twisted.internet.defer.Deferred.html

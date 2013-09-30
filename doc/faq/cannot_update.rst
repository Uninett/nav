==========================
Cricket "Cannot update..."
==========================

When browsing Cricket you may sometimes see graphs that have stopped
graphing data. When checking the log you see statements like this
one::

 [23-Nov-2012 12:11:53*] Cannot update target.rrd: target.rrd: expected 5 data source readings (got 4) from N

What is the problem?
====================

Network equipment change. NAV has detected that it can collect more (or less)
data from this equipment. However, Cricket (or more specifically RRD files)
expect the same number of datapoints every time. It does not adjust
automatically to more or fewer datapoints.

What can I do to fix this?
==========================

Fixing this is surprisingly hard. Or easy. Even fun. It depends on how much you
like xml- and log-files.

The easy way
------------

Delete the RRD file. *Congratulations* - you have now fixed the problem, as Cricket
will generate a new RRD file with the correct number of datapoints. You have
also gotten rid of all history - if this is ok, you are now done. If this is not
ok, read on.

.. image:: who-needs-history.jpg

The hard way
------------

You have decided that history is important (it sure is!). This now requires some
detective work from your side. The steps are:

* Find out what Cricket collected to this RRD file before the error started
  occuring, and what it collects now.
* Use a script to edit the RRD file based on what you discovered.

Sounds easy right?

Finding the difference
^^^^^^^^^^^^^^^^^^^^^^

In the Cricket log-files, the line that causes an error precedes the actual error.

In our example::

 [23-Nov-2012 12:11:53 ] Retrieved data for target (): 7,28624952,38483912,8973203
 [23-Nov-2012 12:11:53*] Cannot update /path/to/target.rrd: /path/to/target.rrd: expected 5 data source readings (got 4) from N

Cricket tried to collect data for "target". It collected data successfully, but
when it tried to store it the error occured. So, what did Cricket collect? We
have to head to Cricket's config to found out.

There are two scenarioes

#. You collect too few datapoints. ``expected 5 data source readings (got
   4)``. This means we need to remove a datasource from the RRD file.
#. You collect too many datapoints. ``expected 4 data source readings (got
   5)``. This means we need to add a datasource to the RRD file.

In our scenario we collect too few datapoints. Or, to put it more correctly, the
RRD file has one datasource too many. We need to remove that one. But which one?
Which of the five datasources in the file do we need to remove? 

Your best bet is to compare the values from before the error happened and
see what is more likely. Lets do that in this case::
 
 [21-Nov-2012 12:11:51 ] Retrieved data for target (): 0,7,28624824,38484040,8886801
 [23-Nov-2012 12:11:53 ] Retrieved data for target (): 7,28624952,38483912,8973203

In this case it's rather obvious. In other cases it may not be, or the log-files
may not be there or it seemed obvious but was wrong. Life is hard, but the worst
that may happen is some skewed data (or angry boss).

Datasources in RRD files are 0-indexed, so let's enumerate the datasources::

  ds0 ds1     ds2       ds3       ds4
  0,    7, 28624824, 38484040, 4242221020

Thus we need to remove datasource 0 (zero). *TADA!*


Editing the RRD file
^^^^^^^^^^^^^^^^^^^^

Ok, with that done the hard part is over. Now we just have to run the script on
the correct RRD file:

.. code-block:: sh
  
  # To add a datasource
  sudo -u navcron python -m nav.rrd.rrdtool_utils -f /path/to/target.rrd -a ds0
  # To remove a datasource
  sudo -u navcron python -m nav.rrd.rrdtool_utils -f /path/to/target.rrd -r ds0

After this is done everything should be ok. Great! If not, feel free to ask for
help on IRC or email.



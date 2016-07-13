===================================
Debugging "gaps in graphs" syndrome
===================================

This document discusses various causes of missing Graphite data, AKA gappy
graphs AKA holy graphs. You should verify each issue in the order they are
listed.


UDP packets are being dropped
=============================

Because NAV sends data to Carbon using UDP, there is no guaranteed data
reception. This could be solved by using TCP, but with a considerable
performance penalty. As data collection in NAV is very bursty, it has occurred
that the kernel's UDP receive buffer has overflowed, causing the kernel to
drop packets. This leads to gaps in the graphs.

Verify packet drops
-------------------

On Linux, to verify that packets are being dropped, you can look in the
:file:`/proc/net/udp` file and find the line with the local port the Carbon
daemon is listening to (default port **2003**, or **07D3** in hex). The number
of packets dropped since the daemon started is shown in the last column. To
output only this number, use:

.. code-block:: console

  $ awk '$2~/07D3/{print $NF}' /proc/net/udp
  4031

If this number keeps increasing, you are affected by the packet dropping
issue.


Increasing the UDP receive buffer
---------------------------------

If packets are being dropped, you can try to increase the kernel's network
receive buffer to avoid this. On Linux this can be done with the following
commands:

.. code-block:: sh

  sysctl net.core.rmem_max                  # See current setting
  sysctl -w net.core.rmem_max=16777216      # Set max buffer to 16MB
  sysctl -w net.core.rmem_default=16777216  # Set default buffer to 16MB

Experiment with different values until the packet dropping stops. You need to
restart the carbon daemon (``carbon-cache`` or ``carbon-relay``, depending on
your setup) to make the changes take effect.

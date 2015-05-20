===============
Tuning Graphite
===============

Handling gaps in the graphs
===========================

Because NAV sends data to Carbon using UDP there is no guaranteed data
reception. This could be solved by using TCP, but with a considerable
performance penalty. As data collection in NAV is very bursty, it has occured
that the kernel's UDP receive buffer has been filled up, causing the kernel to
drop packets. This leads to gaps in the graphs.

Verify drops
------------

On Linux, to verify that packets are being dropped you can look in the
/proc/net/udp file and find the line with the local port Carbon listens to
(default port 07D3, that is 2003 in hex). The drops, if any, are visible in the
last column. Or you can run this command, that outputs the number of packets
dropped since carbon-cache started::

  awk '$2~/07D3/{print $NF}' /proc/net/udp
  4031

Increasing the UDP receive buffer
---------------------------------

If packets are being dropped, then you can try to increase the kernel's network
receive buffer to avoid this. On Linux this is done with the following command::

  sysctl net.core.rmem_max                  # See current setting
  sysctl -w net.core.rmem_max=16777216      # Set max buffer to 16MB
  sysctl -w net.core.rmem_default=16777216  # Set default buffer to 16MB

Experiment with different values to see when there are no more dropped
packets. You may have to restart the carbon-cache to make the changes take
effect.

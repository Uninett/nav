#!/bin/sh
# -----------------------------------------------------------------------
# Shell script snmp_forward.sh
# Create an SNMP tunnel to remote Agent through a hop host
#
# Inspired from:
#   http://www.morch.com/2011/07/05/forwarding-snmp-ports-over-ssh-using-socat/
# See also:
#   https://gist.github.com/n-st/8886963
# Created by Vegard Vesterheim (<vegardv@uninett.no>) 2017-04-07
# -----------------------------------------------------------------------

PROGNAME=$0

snmp_agent=${1:-158.38.12.155}
hop_host=${2:-teknobyen-vk.uninett.no}
tunnel_port=${3:-10000}

remote_tunnel ()
{
    ssh -f -L${tunnel_port}:127.0.0.1:${tunnel_port} $hop_host socat -T10 TCP4-LISTEN:${tunnel_port},fork UDP4:${snmp_agent}:161
}

remote_tunnel

echo "local tunnel..."
sudo socat UDP4-LISTEN:161,fork TCP4:localhost:${tunnel_port}

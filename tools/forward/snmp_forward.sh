#!/bin/bash
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
PGID=$$

snmp_agent=${1:-158.38.12.155}
hop_host=${2:-teknobyen-vk.uninett.no}
tunnel_port=${3:-10000}

remote_tunnel ()
{
    echo "Setting up SSH tunnel to $snmp_agent via $hop_host ..."
    if [[ "$snmp_agent" == *":"* ]]; then
        echo "$snmp_agent looks like an IPv6 address, using an IPv6 tunnel"
        remote_addr=UDP6:\\[${snmp_agent}\]:161
    else
        remote_addr=UDP4:${snmp_agent}:161
    fi
    ssh -tt -o ConnectTimeout=4 -L${tunnel_port}:127.0.0.1:${tunnel_port} $hop_host socat -T10 TCP4-LISTEN:${tunnel_port},fork ${remote_addr}
}

local_tunnel ()
{
    echo "Setting up local socat tunnel to SSH tunnel..."
    sudo socat UDP4-LISTEN:161,fork TCP4:localhost:${tunnel_port}
}


# Ensure everything in process group is stopped if either tunnel process dies
trap "echo A tunnel subprocess died, stopping all forwarding; kill -HUP -$PGID" CHLD

remote_tunnel &
local_tunnel &
wait  # Just wait for all background processes to die


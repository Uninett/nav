# SNMPv3 enabled SNMP daemon for SNMPv3 testing

This directory defines a simple docker image for a NET-SNMP-based SNMP daemon
that is enabled for responding to SNMPv3 requests.

## Building the image

```sh
docker build -t snmpd .
```

## Running a container to respond to SNMP locally

```sh
docker run --name snmpd -p 161:161/udp snmpd
```

## Authentication and privacy

Using the SNMPv3 user security model (USM), this image sets up a read&write user
named `myv3user`, with an authentication password of `my_authpass`, using AES
encryption for security with a privacy password of `my_privpass`.

For SNMP v1 or v2c communication, it sets up a default read-only community of
`public` and a read-write community of `private`.

## Local testing

The entirety of the daemon's mib view can be queried using SNMPv3 by running
the following `snmpwalk` command:

```sh
snmpwalk -v3 -l authPriv -u myv3user -a SHA -A "my_authpass" -x AES -X "my_privpass" localhost
```

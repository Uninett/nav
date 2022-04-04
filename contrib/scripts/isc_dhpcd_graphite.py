#!/usr/bin/env python3
"""Docs here"""

import argparse
from binascii import hexlify
from collections import namedtuple
import json
from math import trunc
import pathlib
import pickle
import struct
import subprocess
import sys
from time import time

DEFAULT_PREFIX = "nav.dhcp"
DEFAULT_CONFIG_FILE = "/etc/dhcpd/dhcpd.conf"
DEFAULT_CMD_PATH = pathlib.Path("/usr/bin/dhcpd-pools")
DEFAULT_PROTOCOL = 2  # Python 3: 3, Python 3.8+: 4
DEFAULT_PORT = "2004"

PICKLE_PROTOCOL = range(0, pickle.HIGHEST_PROTOCOL + 1)
FLAGS = "-f j"
METRIC_MAPPER = {
    "defined": "max",
    "used": "cur",
    "touched": "touch",
    "free": "free",
}


Metric = namedtuple("Metric", ["path", "value", "timestamp"])


# parse comand line flags
def parse_args():
    parser = argparse.ArgumentParser(description="Send dhcp stats to graphite")
    parser.add_argument(
        "server",
        help="Graphite server to send data to",
        type=str,
    )
    parser.add_argument(
        "--port",
        help="Port of Graphite server, if not on 2003 (text) or 2004 (pickle)",
        type=str,
    )
    parser.add_argument(
        "-f",
        "--config-file",
        type=pathlib.Path,
        help="Complete path to dhcpd-pools config-file. Usually located in /etc/dhcpd/",
        default=DEFAULT_CONFIG_FILE,
    )
    parser.add_argument(
        "-C",
        "--command",
        help="Path to dhcpd-pools command",
        type=pathlib.Path,
        default=DEFAULT_CMD_PATH,
    )
    parser.add_argument(
        "-p", "--prefix",
        help="Path prefix to use for the metric, overriding the default",
        type=str,
        default=DEFAULT_PREFIX,
    )
    parser.add_argument(
        "-l", "--location",
        help="Location, if any, to append to the metric prefix",
        type=str,
    )
    protocol_choices = ("text",) + tuple(str(p) for p in PICKLE_PROTOCOL)
    parser.add_argument(
        "-P",
        "--protocol",
        help="Protocol to use to send to graphite server",
        choices=protocol_choices,
        default=str(DEFAULT_PROTOCOL),
        type=str,
    )
    parser.add_argument(
        "-n",
        "--noop",
        action="store_true",
        help="Do not send metrics to graphite, print what would be sent instead",
    )
    args = parser.parse_args()
    try:
        protocol = int(args.protocol)
    except ValueError:
        pass
    else:
        args.protocol = protocol
    if not args.port:
        if isinstance(args.protocol, int):
            args.port = "2004"
        else:
            args.port = "2003"
    args.actual_prefix = args.prefix
    if args.location:
        args.actual_prefix += f".{args.location}"
    return args


# run command and store json output
def exec_dhcpd_pools(config_file, cmd_path=DEFAULT_CMD_PATH, cmd_flags=""):
    flags = cmd_flags.split()
    default_flags = f"-c {config_file} {FLAGS}".split()
    cmd = [cmd_path] + list(default_flags) + list(flags)
    result = subprocess.run(cmd, capture_output=True)
    if result.returncode:
        sys.exit(result.stderr)
    return json.loads(result.stdout)


# reformat the data
def _clean_vlan(location):
    return location.split("_", 1)[0]


def _tuplify(jsonblob, prefix):
    timestamp = trunc(time())
    data = jsonblob["shared-networks"]
    output = list()
    for vlan_stat in data:
        vlan = _clean_vlan(vlan_stat["location"])
        for key, metric in METRIC_MAPPER.items():
            path = f"{prefix}.{vlan}.{metric}"
            value = vlan_stat[key]
            output.append(Metric(path, value, timestamp))
    return output


def render(jsonblob, prefix, protocol=DEFAULT_PROTOCOL):
    if isinstance(protocol, int):
        return _render_pickle(jsonblob, prefix, protocol)
    return _render_text(jsonblob, prefix)


def _render_text(jsonblob, prefix):
    template = "{metric.path} {metric.value} {metric.timestamp}\n"
    input = _tuplify(jsonblob, prefix)
    output = []
    for metric in input:
        line = template.format(metric=metric)
        output.append(line)
    return "".join(output).encode("ascii")


def _render_pickle(jsonblob, prefix, protocol):
    input = _tuplify(jsonblob, prefix)
    output = []
    for metric in input:
        output.append((metric.path, (metric.timestamp, metric.value)))
    payload = pickle.dumps(output, protocol=protocol)
    header = struct.pack("!L", len(payload))
    message = header + payload
    return message


# send the data
def send_to_graphite(metrics_blob, server, port):
    return


def main():
    args = parse_args()
    jsonblob = exec_dhcpd_pools(args.config_file, args.command)
    output = render(jsonblob, args.actual_prefix, args.protocol)
    if args.noop:
        if args.protocol == "text":
            print(output.decode('ascii'))
        else:
            print(hexlify(output).decode('ascii'))
    else:
        send_to_graphite(output, args.server, args.port)


if __name__ == "__main__":
    main()

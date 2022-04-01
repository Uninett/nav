#!/usr/bin/env python3
"""Docs here"""

import subprocess
import argparse
import json
import sys

DEFAULT_PREFIX = 'nav.dhcp'
DEFAULT_CONFIG_FILE_IPv4 = "/etc/dhcpd/dhcpd-ip4.conf"
DEFAULT_CONFIG_FILE_IPv6 = "/etc/dhcpd/dhcpd-ip6.conf"
DEFAULT_CMD_PATH = "/usr/bin/dhcpd-pool"
DEFAULT_PROTOCOL=2

FLAGS = "-f j"
METRIC_MAPPER = {
    'defined': 'max',
    'used': 'cur',
    'touched': 'touch',
    'free': 'free',
}

# parse comand line flags


# run command and store json output
def exec_dhcpd_pool(config_file, cmd_path=DEFAULT_CMD_PATH, cmd_flags=''):
    flags = cmd_flags.split()
    default_flags = f"-c {config_file} {FLAGS}".split()
    cmd = [cmd_path] + list(default_flags) + list(flags)
    result = subprocess.run(cmd, capture_output=True)
    if result.returncode:
        sys.exit(result.stderr)
    return json.loads(result.stdout)


# reformat the data
def tuplify(jsonblob, prefix):
    data = jsonblob["shared-networks"]
    output = list()
    timestamp = 'x'
    for vlan_stat in data:
        vlan = data["location"].split("_", 1)[0]
        for key, metric in METRIC_MAPPER.items():
            path = f'{prefix}.{vlan}.{metric}'
            value = data["key"]
            output.append(tuple(path, (timestamp, value)))
    return metric_tuples


def render_text(jsonblob, prefix):
    template = "{metric[0]} {metric[1][0]} {metric[1][0]}\n"
    output = tuplify(jsonblob, prefix)
    for metric in output:
            line = TEMPLATE.format(metric)
            output.append(line)
    return ''.join(output)


def render_pickle(jsonblob, prefix, protocol=DEFAULT_PROTOCOL):
    output = tuplify(jsonblob, prefix)
    payload = pickle.dumps(output, protocol=2)
    header = struct.pack("!L", len(payload))
    message = header + payload
    return message


# send the data
def send_to_graphite(metrics_blob, server):
    return


if __name__ == '__main__':
    pass
    # get command-line flags
    # - metric-prefix
    # - graphite server name
    # - port (2004 by default)
    # - location (optional, string)
    # 

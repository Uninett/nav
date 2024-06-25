from dataclasses import dataclass
from enum import Enum
from nav.metrics import carbon
from typing import Iterator

class DhcpMetricKey(Enum):
    MAX = "total addresses"
    CUR = "assigned addresses"
    TOUCH = "touched addresses"
    FREE = "free addresses"

    def __str__(self):
        return self.name.lower() # For use in graphite path

@dataclass
class DhcpMetric:
    timestamp: int
    vlan: int # the vlan this metric tracks
    key: DhcpMetricKey
    value: int

class DhcpMetricSource:
    """
    Superclass for all classes that wish to collect metrics from a
    specific line of DHCP servers and import the metrics into NAV's
    graphite server. Subclasses need to implement `fetch_metrics`.
    """
    graphite_prefix: str

    def __init__(self, graphite_prefix="nav.dhcp"):
        self.graphite_prefix = graphite_prefix

    def fetch_metrics(self) -> Iterator[DhcpMetric]:
        """
        Fetch total addresses, assigned addresses, touched addresses,
        and free adddresses for each vlan of the DHCP server.

        None of the DHCP server packages that has had a
        DhcpMetricSource class definition so far has any way to
        explicitly define which subnet or pool belongs to which
        vlan. The way we figure out which subnet or pool belongs to
        which vlan, differs between the DHCP server packages; usually
        it is possible to give each subnet or pool or group of
        subnets/pools a name, ID, or tag.  The convention is that this
        name, ID or tag is the vlan-number of that specific subnet or
        pool or group of subnets/pools.

        Each subclass of DhcpMetricSource should document how it finds
        out what vlan a subnet/pool belongs to. It should be clear
        whether or not it relies on any specific conventions that the
        administrator of a DHCP server must follow.

        TODO: document this properly. (do we need to specify the
        rationale for grouping metrics by vlan and not
        e.g. subnet-prefixes, etc. or is this clear to all users of
        nav?)
        """
        raise NotImplementedError
    def fetch_metrics_to_graphite(self, host, port):
        graphite_metrics = []
        for metric in self.fetch_metrics():
            graphite_path = f"{self.graphite_prefix}.vlan{metric.vlan}.{metric.key}"
            datapoint = (metric.timestamp, metric.value)
            graphite_metrics.append((graphite_path, datapoint))
        carbon.send_metrics_to(graphite_metrics, host, port)

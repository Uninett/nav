from dataclasses import dataclass
from enum import Enum
from IPy import IP
from nav.metrics import carbon, CONFIG
from nav.metrics.templates import metric_path_for_subnet_dhcp, metric_path_for_ipdev_subnet_dhcp
from typing import Iterator
from datetime import datetime


class DhcpMetricKey(Enum):
    TOTAL = "total"  # total addresses managed by dhcp
    ASSIGNED = "assigned"  # assigned addresses

    def __str__(self):
        return self.value  # graphite key


@dataclass(frozen=True)
class DhcpMetric:
    timestamp: datetime
    subnet_prefix: IP
    key: DhcpMetricKey
    value: int


class DhcpMetricSource:
    """
    Superclass for all classes that wish to collect metrics from a
    specific line of DHCP servers and import the metrics into NAV's
    graphite server. Subclasses need to implement `fetch_metrics`.

    The `fetch_metrics` docstring specifies which metrics are
    collected.
    """
    def __init__(self, address, port):
        """
        All subclasses that collect metrics from a DHCP server must
        specify the address and port of the server it collects metrics
        from so that we can reliably discern the metrics collected
        from different servers (it is for example possible that two
        servers serve the same subnet and hence it is not viable to
        discern the metrics collected solely based on the subnet it is
        for).
        """
        self.address = address
        self.port = port

    def fetch_metrics(self) -> Iterator[DhcpMetric]:
        """
        Fetch DhcpMetrics having keys `TOTAL` and `ASSIGNED` for each subnet of the
        DHCP server at current point of time.
        """
        raise NotImplementedError

    def fetch_metrics_to_graphite(
        self, host=CONFIG.get("carbon", "host"), port=CONFIG.getint("carbon", "port")
    ):
        """
        Fetch metrics describing total amount of addresses
        (DhcpMetricKey.TOTAL) and amount of addresses that have been
        assigned to a client (DhcpMetricKey.ASSIGNED) for each subnet
        of the DHCP server at current point of time and send the
        metrics to the graphite server at `host` on `port`.
        """
        graphite_metrics = []
        for metric in self.fetch_metrics():
            metric_path = metric_path_for_ipdev_subnet_dhcp(
                metric.subnet_prefix, str(metric.key), self.address, self.port
            )
            datapoint = (metric.timestamp, metric.value)
            graphite_metrics.append((metric_path, datapoint))
        carbon.send_metrics_to(graphite_metrics, host, port)

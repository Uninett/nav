from dataclasses import dataclass
from enum import Enum
from IPy import IP
from nav.metrics import carbon, CONFIG
from nav.metrics.names import escape_metric_name
from typing import Iterator
from datetime import datetime


class DhcpMetricKey(Enum):
    TOTAL = "total"  # total addresses managed by dhcp
    ASSIGNED = "assigned"  # assigned addresses
    def __str__(self):
        return self.value # graphite key


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
    """

    graphite_prefix: str

    def __init__(self, graphite_prefix="nav.dhcp"):
        self.graphite_prefix = graphite_prefix

    def fetch_metrics(self) -> Iterator[DhcpMetric]:
        """
        Fetch DhcpMetrics having keys `MAX`, `CUR`, `TOUCH` and `FREE`
        for each subnet of the DHCP server at current point of time.
        """
        raise NotImplementedError

    def fetch_metrics_to_graphite(
            self,
            host=CONFIG.get("carbon", "host"),
            port=CONFIG.getint("carbon", "port")
    ):
        graphite_metrics = []
        for metric in self.fetch_metrics():
            graphite_path = f"{self.graphite_prefix}.{escape_metric_name(metric.subnet_prefix.strNormal())}.{metric.key}"
            datapoint = (metric.timestamp, metric.value)
            graphite_metrics.append((graphite_path, datapoint))
        carbon.send_metrics_to(graphite_metrics, host, port)

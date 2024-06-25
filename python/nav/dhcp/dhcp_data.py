from typing import Iterator
from dataclasses import dataclass
from nav.metrics import carbon

@dataclass
class DhcpMetric:
    timestamp: int
    vlan: int
    key: str
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
        raise NotImplementedError
    def fetch_metrics_to_graphite(self, host, port):
        graphite_metrics = []
        for metric in self.fetch_metrics():
            graphite_path = f"{self.graphite_prefix}.vlan-{metric.vlan}.{metric.key}"
            datapoint = (metric.timestamp, metric.value)
            graphite_metrics.append((graphite_path, datapoint))
        carbon.send_metrics_to(graphite_metrics, host, port)

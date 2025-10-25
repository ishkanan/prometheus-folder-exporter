"""
Define the metrics we export.
"""
import os

from prometheus_client import Gauge

NAMESPACE = os.environ.get("METRICS_NAMESPACE", "folder-exporter")

TOTAL_SIZE = Gauge(
    "total_size_bytes",
    "Total Size of the folder (in bytes)",
    namespace=NAMESPACE,
    labelnames=("folder",)
)

LATEST_MTIME = Gauge(
    "latest_mtime",
    "Newest modified file in the folder (as unix timestamp)",
    namespace=NAMESPACE,
    labelnames=("folder",)
)

OLDEST_MTIME = Gauge(
    "oldest_mtime",
    "Oldest modified file in the folder (as unix timestamp)",
    namespace=NAMESPACE,
    labelnames=("folder",)
)

ENTRIES_COUNT = Gauge(
    "entries_count",
    "Total number of entries (files, directories & links) in the folder",
    namespace=NAMESPACE,
    labelnames=("folder",)
)

LAST_SCANNED = Gauge(
    "last_scanned_ns",
    "Last time this folder was scanned (as unix timestamp)",
    namespace=NAMESPACE,
    labelnames=("folder",)
)

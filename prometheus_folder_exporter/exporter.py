import os
import time
from dataclasses import dataclass
from typing import Never, Optional

from . import metrics

from prometheus_client import start_http_server

type Timestamp = float
type Seconds = float


@dataclass
class DirInfo:
    path: str
    size: int
    latest_mtime: Timestamp
    oldest_mtime: Timestamp
    entries_count: int


def emit_dir_metrics(info: DirInfo):
    metrics.TOTAL_SIZE.labels(info.path).set(info.size)
    metrics.LATEST_MTIME.labels(info.path).set(info.latest_mtime)
    metrics.OLDEST_MTIME.labels(info.path).set(info.oldest_mtime)
    metrics.ENTRIES_COUNT.labels(info.path).set(
        info.entries_count
    )
    metrics.LAST_SCANNED.labels(info.path).set(time.time())


def scan_dir(path: str) -> Optional[DirInfo]:
    try:
        self_statinfo = os.stat(path)
    except FileNotFoundError:
        # Directory was deleted from the time it was listed and now
        return None

    # Get absolute path of all children of directory
    children = [
        os.path.join(path, c)
        for c in os.listdir(path)
    ]

    # Split into files and directories for different kinds of traversal.
    # We count symlinks as files, but do not resolve them when checking size -
    # but do include them in the mtime calculation.
    files = [
        c
        for c in children
        if os.path.isfile(c) or os.path.islink(c)
    ]
    dirs = [c for c in children if os.path.isdir(c)]

    total_size = self_statinfo.st_size
    latest_mtime = self_statinfo.st_mtime
    oldest_mtime = self_statinfo.st_mtime
    entries_count = len(files) + 1  # Include this directory as an entry

    for f in files:
        # Do not follow symlinks, as that may lead to double counting a symlinked
        # file's size.
        try:
            stat_info = os.stat(f, follow_symlinks=False)
        except FileNotFoundError:
            # File might have been deleted from the time we listed it anda now
            continue
        total_size += stat_info.st_size
        if latest_mtime < stat_info.st_mtime:
            latest_mtime = stat_info.st_mtime
        if oldest_mtime > stat_info.st_mtime:
            oldest_mtime = stat_info.st_mtime

    for d in dirs:
        dirinfo = scan_dir(d)
        if dirinfo is None:
            # The directory was deleted between the time the listing
            # was done and now.
            continue
        total_size += dirinfo.size
        entries_count += dirinfo.entries_count
        if latest_mtime < dirinfo.latest_mtime:
            latest_mtime = dirinfo.latest_mtime
        if oldest_mtime > dirinfo.latest_mtime:
            oldest_mtime = dirinfo.latest_mtime

    info = DirInfo(
        path=path,
        size=total_size,
        latest_mtime=latest_mtime,
        oldest_mtime=oldest_mtime,
        entries_count=entries_count,
    )
    emit_dir_metrics(info)
    return info


def get_subdirs_info(dir_path: str):
    try:
        children = [
            os.path.join(dir_path, c)
            for c in os.listdir(dir_path)
        ]

        dirs = [c for c in children if os.path.isdir(c)]

        for c in dirs:
            scan_dir(c)
    except PermissionError as e:
        if e.errno == 13:
            # See https://github.com/yuvipanda/prometheus-dirsize-exporter/issues/5
            # A file we are trying to open is owned in such a way that we don't have
            # access to it. Ideally this should not really happen, but when it does,
            # we just ignore it and continue.
            return None
        # Any other permission error should be propagated
        raise
    except OSError as e:
        if e.errno == 116:
            # See https://github.com/yuvipanda/prometheus-dirsize-exporter/issues/6
            # Stale file handle, often because the file we were looking at
            # changed in the NFS server via another client in such a way that
            # a new inode was created. This is a race, so let's just ignore and
            # not report any data for this file. If this file was recreated,
            # our next run should catch it
            return None
        # Any other errors should just be propagated
        raise


def start() -> Never:
    parent_dirs = os.environ["EXPORTED_DIRS"].split("|")
    wait_time_minutes = int(os.environ.get("SCAN_DELAY_MINS", 5))
    port = int(os.environ.get("PORT", 8000))

    print("Configuration:")
    print(f"--> Exported folders = {parent_dirs}")
    print(f"--> Wait time = {wait_time_minutes}m")
    print(f"--> Port = {port}")

    start_http_server(port)

    print("Started metrics server...")

    while True:
        for parent_dir in parent_dirs:
            get_subdirs_info(parent_dir)

        time.sleep(wait_time_minutes * 60)

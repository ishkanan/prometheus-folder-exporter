# prometheus-folder-exporter

Export folder metrics to Prometheus.

## What does it do?

This project provides a Prometheus-digestible endpoint that periodically scans
a set of folders and exports the following information about each folder:

- Total size (in bytes)
- Total entry count (files, folders and symlinks)
- Last modified time (recursively determined)
- Last scanned time

It recursively scans each folder and generates a metric for each sub-folder. Stats for a set of siblings are included in the parent stats, like so:

```
# HELP folder_exporter_total_size_bytes Total Size of the folder (in bytes)
# TYPE folder_exporter_total_size_bytes gauge
folder_exporter_total_size_bytes{folder="/logs"} 2000.0
folder_exporter_total_size_bytes{folder="/logs/2025-01-01"} 1500.0
folder_exporter_total_size_bytes{folder="/logs/2025-01-02"} 500.0
```

Note that folder contents might change during a scan. This can affect the accuracy of the final results. Symlinks are not followed.

## Installation

It can be set up to run natively (Python 3.13+):

```
$ pip install -r requirements.txt
```

Or built into a Docker image:

```
$ docker buildx build --no-cache -t prometheus-folder-exporter:latest .
```

And if your Docker engine supports multi-arch (MacOS Docker Desktop does):

```
$ docker buildx build --platform linux/amd64,linux/arm64 --no-cache -t prometheus-folder-exporter:latest .
```

## Configuration

The app accepts runtime configuration via environment variables:

| Variable          | Required | Default         | Description
| :---------------- | :------: | :-------------- | :----------
| EXPORTED_DIRS     | Y        |                 | Pipe-separated string of folders to scan
| METRICS_NAMESPACE |          | folder_exporter | Metric name prefix
| PORT              |          | 8000            | Port to listen on
| SCAN_DELAY_MINS   |          | 5               | Minimum delay (mins) between scans

## Running

After installation, run the app natively with:

```
$ EXPORTED_DIRS="/home/user1/Desktop|/home/user2/Desktop" python -m prometheus_folder_exporter
```

Or with the Docker CLI:

```
$ docker run --rm -u root -e EXPORTED_DIRS="/data" -p 8000:8000 -v /home/user1/Desktop:/data/desktop1:ro -v /home/user2/Desktop:/data/desktop2:ro prometheus-folder-exporter:latest
```

Or via Docker Compose:

```
services:
  folder-exporter:
    container_name: folder-exporter
    image: prometheus-folder-exporter:latest
    restart: unless-stopped
    environment:
      - EXPORTED_DIRS=/data
    volumes:
      - /home/user1/Desktop:/data/desktop1:ro
      - /home/user2/Desktop:/data/desktop2:ro
    ports:
      - 8000:8000
    user: root
```

### Docker notes

Each volume can be mounted as a sub-folder in `/data` and set `EXPORTED_DIRS=/data`. This is the most convenient way of scanning multiple folders and ensures unique `folder` labels across all metrics.

Be sure to run the container as a user that has permissions to traverse the folders. The examples above use `root`, but ultimately it will be based on your security preferences.

It is also recommended to pass `:ro` to each volume mount to prevent the container from interfering with the filesystem.

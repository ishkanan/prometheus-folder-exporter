FROM python:3.13-alpine

ADD prometheus_folder_exporter /tmp/src

RUN apk update && \
    apk add tini && \
    pip install -r /tmp/src/requirements.txt && \
    mkdir /data

ENV EXPORTED_DIRS
ENV METRICS_NAMESPACE
ENV PORT
ENV SCAN_DELAY_MINS

ENTRYPOINT ["tini", "--"]

CMD ["/usr/bin/python", "-m", "prometheus_folder_exporter"]

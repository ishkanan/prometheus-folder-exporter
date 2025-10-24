FROM python:3.13-alpine

ADD . /app

RUN apk update && \
    apk add tini && \
    pip install -r /app/requirements.txt && \
    mkdir /data

ENTRYPOINT ["tini", "--"]

WORKDIR /app

CMD ["/usr/local/bin/python", "-m", "prometheus_folder_exporter"]

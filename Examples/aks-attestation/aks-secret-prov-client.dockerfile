FROM ubuntu:18.04

RUN apt-get update \
    && env DEBIAN_FRONTEND=noninteractive apt-get install -y git build-essential

COPY client.c /client.c
RUN client.c -o min_client && cp min_client /usr/local/bin
COPY ssl/ca.crt /ca.crt

ENTRYPOINT ["min_client"]

FROM alpine:3.21

RUN apk add --no-cache smartmontools

COPY smartctl_exporter-0.14.0.linux-amd64/smartctl_exporter /bin/smartctl_exporter

RUN chmod 0755 /bin/smartctl_exporter

EXPOSE 9633

USER root
ENTRYPOINT ["/bin/smartctl_exporter"]

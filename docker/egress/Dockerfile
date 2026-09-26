FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get install -y --no-install-recommends squid iptables util-linux netcat-openbsd \
    && test "$(id -u proxy)" = "13" \
    && test "$(id -g proxy)" = "13" \
    && rm -rf /var/lib/apt/lists/*

COPY squid.conf /etc/squid/squid.conf
COPY egress-entrypoint.sh /usr/local/bin/egress-entrypoint.sh
RUN chmod 0755 /usr/local/bin/egress-entrypoint.sh

EXPOSE 3128
ENTRYPOINT ["/usr/local/bin/egress-entrypoint.sh"]

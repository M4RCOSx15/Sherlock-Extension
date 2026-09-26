#!/bin/sh
set -eu

: "${SCANNER_CLIENT_IP:?SCANNER_CLIENT_IP is required}"

# Apply controls inside this container's network namespace. DNS is allowed
# only through Docker's embedded resolver; outbound web TCP is limited to 80/443.
iptables -F OUTPUT
iptables -P OUTPUT DROP
iptables -A OUTPUT -o lo -j ACCEPT
iptables -A OUTPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
iptables -A OUTPUT -d 127.0.0.11/32 -p udp --dport 53 -j ACCEPT
iptables -A OUTPUT -d 127.0.0.11/32 -p tcp --dport 53 -j ACCEPT

for cidr in \
  0.0.0.0/8 \
  10.0.0.0/8 \
  100.64.0.0/10 \
  127.0.0.0/8 \
  169.254.0.0/16 \
  172.16.0.0/12 \
  192.0.0.0/24 \
  192.0.2.0/24 \
  192.88.99.0/24 \
  192.168.0.0/16 \
  198.18.0.0/15 \
  198.51.100.0/24 \
  203.0.113.0/24 \
  224.0.0.0/4 \
  240.0.0.0/4 \
  255.255.255.255/32
do
  iptables -A OUTPUT -d "$cidr" -j REJECT
done

iptables -A OUTPUT -p tcp -m multiport --dports 80,443 -j ACCEPT

# The proxy cannot open IPv6 sockets to any destination. This prevents an
# IPv6 route or DNS answer from bypassing the IPv4 destination policy.
ip6tables -F OUTPUT
ip6tables -P OUTPUT DROP
ip6tables -A OUTPUT -o lo -j ACCEPT
ip6tables -A OUTPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

# Compose mounts /run/squid owned by the unprivileged Squid user (uid/gid 13).
# Avoid chown here. SETPCAP is available only for this root bootstrap so
# setpriv can clear every capability before starting Squid as the proxy user.
exec setpriv --bounding-set=-all --inh-caps=-all --reuid=proxy --regid=proxy --init-groups /usr/sbin/squid -N -f /etc/squid/squid.conf

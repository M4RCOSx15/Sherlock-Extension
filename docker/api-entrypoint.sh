#!/bin/sh
set -eu

: "${SCRAPER_PROXY_IP:?SCRAPER_PROXY_IP is required}"

# Fail closed if this runtime cannot apply the container-local egress policy.
iptables -F OUTPUT
iptables -P OUTPUT DROP
iptables -A OUTPUT -o lo -j ACCEPT
iptables -A OUTPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
iptables -A OUTPUT -d 127.0.0.11/32 -p udp --dport 53 -j ACCEPT
iptables -A OUTPUT -d 127.0.0.11/32 -p tcp --dport 53 -j ACCEPT
iptables -A OUTPUT -d "${SCRAPER_PROXY_IP}/32" -p tcp --dport 3128 -j ACCEPT

# No IPv6 egress is enabled in this stack. Keep it denied if the host exposes
# an IPv6 route anyway.
ip6tables -F OUTPUT
ip6tables -P OUTPUT DROP
ip6tables -A OUTPUT -o lo -j ACCEPT
ip6tables -A OUTPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

# SETPCAP is available only for this root bootstrap so setpriv can clear the
# capability sets before dropping to the unprivileged application user.
exec setpriv --bounding-set=-net_admin,-setuid,-setgid,-setpcap --inh-caps=-all --reuid=pwuser --regid=pwuser --init-groups "$@"

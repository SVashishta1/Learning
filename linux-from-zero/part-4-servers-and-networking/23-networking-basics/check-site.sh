#!/usr/bin/env bash
# check-site.sh - follows a web request step by step and tells you WHERE it breaks.
#   1. DNS: can we turn the name into an IP address?
#   2. TCP: can we open a connection to the port?
#   3. HTTP: does the server answer, how fast, with which status code?
# Usage:   ./check-site.sh URL
# Example: ./check-site.sh https://pypi.org     ./check-site.sh http://localhost:8080
# Exit codes: 0 = all good, 1 = DNS failed, 2 = connection failed, 3 = HTTP problem, 4 = bad usage

set -uo pipefail

url="${1:-}"
if [[ -z "$url" ]]; then
  echo "Usage: $0 URL   (for example: $0 https://pypi.org)" >&2
  exit 4
fi

# --- Take the URL apart with bash pattern tricks -----------------------------
scheme="${url%%://*}"                # %%://* = cut off everything from the first :// -> https
rest="${url#*://}"                   # #*://  = cut off everything up to :// -> pypi.org/simple
hostport="${rest%%/*}"               # cut at the first / -> pypi.org  (or localhost:8080)
host="${hostport%%:*}"               # cut at the first : -> pypi.org
if [[ "$hostport" == *:* ]]; then    # was a port written in the URL?
  port="${hostport##*:}"             # ##*: = keep what is after the last :
elif [[ "$scheme" == "https" ]]; then
  port=443                           # the standard HTTPS port
else
  port=80                            # the standard HTTP port
fi
echo "URL $url -> scheme=$scheme host=$host port=$port"

# --- Step 1: DNS ----------------------------------------------------------------
# getent hosts asks the system resolver, exactly like browsers and curl do (it reads /etc/hosts too).
ip=$(getent hosts "$host" | awk '{print $1; exit}')   # the first address found
if [[ -z "$ip" ]]; then
  echo "1. DNS   FAIL  '$host' does not resolve. Check spelling, /etc/hosts, and: dig $host"
  exit 1
fi
echo "1. DNS   OK    $host -> $ip"

# --- Step 2: TCP connection -------------------------------------------------------
# /dev/tcp/HOST/PORT is a bash trick: opening it opens a TCP connection. timeout 5 = give up after 5 s.
if timeout 5 bash -c "exec 3<>/dev/tcp/$ip/$port" 2> /dev/null; then
  echo "2. TCP   OK    port $port on $ip accepts connections"
else
  echo "2. TCP   FAIL  cannot connect to $ip port $port (server down, wrong port, or a firewall)"
  exit 2
fi

# --- Step 3: HTTP ----------------------------------------------------------------
# -o /dev/null = throw the page away, -s = silent, -w = print these timing variables when done
result=$(curl -o /dev/null -s -m 15 -w '%{http_code} %{time_namelookup} %{time_connect} %{time_appconnect} %{time_starttransfer} %{time_total}' "$url")
read -r code t_dns t_conn t_tls t_first t_total <<< "$result"   # split the 6 numbers into variables

echo "3. HTTP  status $code   (dns ${t_dns}s, connect ${t_conn}s, tls ${t_tls}s, first byte ${t_first}s, total ${t_total}s)"
if [[ "$code" =~ ^[23] ]]; then      # 2xx = success, 3xx = redirect: both mean the server works
  echo "All good."
  exit 0
else
  echo "The server answered, but with status $code (000 = no proper HTTP answer)."
  exit 3
fi

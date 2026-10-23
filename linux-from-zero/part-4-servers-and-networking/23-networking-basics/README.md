# 23 · Networking basics

**What you'll build:** your own web server on port 8080, a made-up web address (`myapp.test`) that points to it, and `check-site.sh`, a mini network detective that follows a request step by step (DNS → connection → HTTP) and tells you exactly where it breaks.
**Like you're 5:** the internet is a giant postal system. An **IP address** is a building's street address, a **port** is the flat number inside the building, and **DNS** is the phone book that turns a name ("pypi.org") into an address. A web request is a letter, and the server's reply is the letter that comes back.
**Time:** ~90 min · **Builds on:** [22 · Disks and the filesystem tree](../22-disks-and-the-filesystem-tree) · **Needs:** `python3` (comes with Ubuntu), `curl`, `dig` (`sudo apt install dnsutils`), internet access for some steps

## Why this matters
Every AI product is a network conversation: your app calls the Claude API over HTTPS, a RAG service talks to a vector database on port 5432, Ollama listens on port 11434. "It can't connect" is the bug you will see most as an engineer at a customer site, and the fix is always found the same way: Does the name resolve? Can I reach the port? What does the server answer? This lesson gives you the tools for each question.

## What you'll learn
- **IP address, port, localhost**: where a program lives on a network, and which door it listens on.
- **DNS**: how names become IP addresses (`dig`, `getent`, `/etc/hosts`).
- **The path of a request**: name lookup → TCP connection → (TLS) → HTTP request → response, and which tool tests each step.
- **The tools**: `ip`, `ss`, `ping`, `curl -v`, `dig`, `traceroute`, read line by line.
- **Listening addresses**: why `127.0.0.1:8000` is private to your computer and `0.0.0.0:8000` is open to the network.

## Before you start
- Install the network tools once (most are already there on Ubuntu):
  ```bash
  sudo apt update
  sudo apt install curl dnsutils iputils-ping traceroute iproute2
  ```
  | Package | Gives you |
  |---|---|
  | `curl` | make web requests from the terminal |
  | `dnsutils` | `dig`, the DNS question tool |
  | `iputils-ping` | `ping` |
  | `traceroute` | `traceroute`, shows each router on the way |
  | `iproute2` | `ip` and `ss` |
- You need `sudo` for step 11 (editing `/etc/hosts`).
- No API key needed.

## Run it
1. From the course folder (`linux-from-zero`), go into this lesson's folder:
   ```bash
   cd part-4-servers-and-networking/23-networking-basics
   ```
2. See where you are on the network:
   ```bash
   ./net-info.sh
   ```
3. Look at your addresses with the `ip` command:
   ```bash
   ip -brief address
   ip route
   ```
   **Command, piece by piece**
   | Piece | Meaning |
   |---|---|
   | `ip` | the modern tool for network settings (replaces the old `ifconfig`) |
   | `-brief` | one short line per network card |
   | `address` (or `a`) | show IP addresses |
   | `ip route` | show the routing table: which way traffic goes. `default via X` = "for everything else, go through router X" |
4. Ask DNS for pypi.org's address (the site where `pip` downloads packages):
   ```bash
   dig pypi.org
   dig +short pypi.org
   ```
5. Is the server reachable at all? Send 4 "are you there?" packets:
   ```bash
   ping -c 4 pypi.org
   ```
   `-c 4` = **c**ount: send 4 and stop (without it, ping runs until Ctrl + C).
6. Which routers does your traffic pass through?
   ```bash
   traceroute -n pypi.org
   ```
   `-n` = show numbers only (faster, no name lookups). Lines of `* * *` are routers that do not answer; that is normal.
7. **Your own server.** Create the website, then start a web server. Open a **second terminal** for this, because the server keeps running:
   ```bash
   bash setup.sh
   cd ~/linux-practice/23/site
   python3 -m http.server 8080
   ```
   **Command, piece by piece**
   | Piece | Meaning |
   |---|---|
   | `python3` | the Python interpreter |
   | `-m http.server` | run Python's built-in module (`-m`) that serves the files of the current folder over HTTP |
   | `8080` | the port to listen on. Ports below 1024 need root, so test servers use 8000, 8080... |
8. Back in the **first terminal**, see your server listening:
   ```bash
   ss -tln
   sudo ss -tlnp | grep 8080
   ```
   **Command, piece by piece**
   | Piece | Meaning |
   |---|---|
   | `ss` | "socket statistics": list network connections |
   | `-t` | TCP only |
   | `-l` | listening sockets only (servers waiting for visitors) |
   | `-n` | show numbers (`8080`), not service names (`http-alt`) |
   | `-p` | show the **p**rogram (needs `sudo` to see other users' programs) |
9. Talk to it with curl, first plainly, then with every detail shown:
   ```bash
   curl http://localhost:8080
   curl -v http://localhost:8080
   ```
10. Ask only for the headers, and see what a missing page returns:
    ```bash
    curl -I http://localhost:8080/
    curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8080/nope
    ```
    | Piece | Meaning |
    |---|---|
    | `-I` | fetch only the headers (a HEAD request) |
    | `-s` | silent: no progress bar |
    | `-o /dev/null` | write the page into the bin |
    | `-w "%{http_code}\n"` | after the request, print only the status code and a new line |
11. Give your server a name. Add a line to `/etc/hosts`, the computer's own little phone book, which is checked **before** DNS:
    ```bash
    echo "127.0.0.1   myapp.test" | sudo tee -a /etc/hosts
    getent hosts myapp.test
    curl http://myapp.test:8080
    ```
    **Command, piece by piece**
    | Piece | Meaning |
    |---|---|
    | `echo "127.0.0.1   myapp.test"` | the new line: address, spaces, name |
    | `\|` | pipe it into the next command |
    | `sudo tee -a /etc/hosts` | `tee` writes what it receives into a file (and to the screen); `-a` = append; `sudo` because `/etc/hosts` belongs to root. (`sudo echo ... >> /etc/hosts` does NOT work: the `>>` is done by your own shell, without sudo) |
    | `getent hosts myapp.test` | look a name up exactly the way programs do (`/etc/hosts` first, then DNS) |
12. Run the detective on a working site, your own server, a closed port and a name that does not exist:
    ```bash
    ./check-site.sh https://pypi.org/simple/
    ./check-site.sh http://myapp.test:8080
    ./check-site.sh http://localhost:9999 ; echo "exit code: $?"
    ./check-site.sh https://no-such-name.invalid ; echo "exit code: $?"
    ```
13. Check your work (the server must still be running in the other terminal):
    ```bash
    ./check.sh
    ```
14. Clean up: press **Ctrl + C** in the server terminal, then remove the `/etc/hosts` line:
    ```bash
    sudo sed -i '/myapp.test/d' /etc/hosts
    ```
    `sed -i '/myapp.test/d'` = in place, **d**elete every line containing `myapp.test`.

### What you should see
Step 2 (real output from a test container; on a home computer you will usually see a `192.168.x.x` address and a `wlan0` or `eth0` card, plus your public IP at the end):
```
=== Computer name ===
myserver

=== My IP addresses (ip -brief address) ===
lo               UNKNOWN        127.0.0.1/8
eth0@if18        UP             172.17.0.3/16

=== Default gateway: the router my traffic leaves through (ip route) ===
default via 172.17.0.1 dev eth0

=== DNS servers: who I ask to turn names into IP addresses ===
nameserver 8.8.8.8
nameserver 8.8.4.4

=== Programs listening for connections (ss) ===
Netid State  Recv-Q Send-Q Local Address:Port Peer Address:PortProcess
tcp   LISTEN 0      4096         0.0.0.0:22        0.0.0.0:*
```
Step 4 (real output):
```
; <<>> DiG 9.18.39-0ubuntu0.24.04.8-Ubuntu <<>> pypi.org
;; global options: +cmd
;; Got answer:
;; ->>HEADER<<- opcode: QUERY, status: NOERROR, id: 43237
;; flags: qr rd ra; QUERY: 1, ANSWER: 4, AUTHORITY: 0, ADDITIONAL: 1

;; QUESTION SECTION:
;pypi.org.			IN	A

;; ANSWER SECTION:
pypi.org.		10754	IN	A	151.101.128.223
pypi.org.		10754	IN	A	151.101.0.223
pypi.org.		10754	IN	A	151.101.192.223
pypi.org.		10754	IN	A	151.101.64.223

;; Query time: 0 msec
;; SERVER: 8.8.8.8#53(8.8.8.8) (UDP)
;; WHEN: Thu Oct 22 18:59:14 UTC 2026
;; MSG SIZE  rcvd: 101
```
Step 5 (typical; times depend on where you are):
```
PING pypi.org (151.101.128.223) 56(84) bytes of data.
64 bytes from 151.101.128.223: icmp_seq=1 ttl=57 time=9.81 ms
64 bytes from 151.101.128.223: icmp_seq=2 ttl=57 time=9.64 ms
64 bytes from 151.101.128.223: icmp_seq=3 ttl=57 time=9.70 ms
64 bytes from 151.101.128.223: icmp_seq=4 ttl=57 time=9.66 ms

--- pypi.org ping statistics ---
4 packets transmitted, 4 received, 0% packet loss, time 3005ms
rtt min/avg/max/mdev = 9.640/9.702/9.810/0.065 ms
```
Step 6 (typical):
```
traceroute to pypi.org (151.101.128.223), 30 hops max, 60 byte packets
 1  192.168.1.1  1.212 ms  1.180 ms  1.161 ms
 2  10.20.0.1  8.402 ms  8.390 ms  8.371 ms
 3  * * *
 4  151.101.128.223  9.711 ms  9.689 ms  9.650 ms
```
Step 8 (real output). `0.0.0.0:8080` means "listening on every network card":
```
State  Recv-Q Send-Q Local Address:Port Peer Address:PortProcess
LISTEN 0      5            0.0.0.0:8080      0.0.0.0:*
LISTEN 0      4096         0.0.0.0:22        0.0.0.0:*
LISTEN 0      5            0.0.0.0:8080      0.0.0.0:*    users:(("python3",pid=550,fd=3))
```
Step 9, `curl -v` (real output):
```
* Host localhost:8080 was resolved.
* IPv6: ::1
* IPv4: 127.0.0.1
*   Trying 127.0.0.1:8080...
* Connected to localhost (127.0.0.1) port 8080
> GET / HTTP/1.1
> Host: localhost:8080
> User-Agent: curl/8.5.0
> Accept: */*
>
* HTTP 1.0, assume close after body
< HTTP/1.0 200 OK
< Server: SimpleHTTP/0.6 Python/3.12.3
< Date: Thu, 22 Oct 2026 18:59:52 GMT
< Content-type: text/html
< Content-Length: 152
< Last-Modified: Thu, 22 Oct 2026 18:59:51 GMT
<
<!doctype html>
<html>
  <head><meta charset="utf-8"><title>My tiny server</title></head>
  <body><h1>Hello from my own web server!</h1></body>
</html>
* Closing connection
```
And in the server terminal, one line per visit:
```
Serving HTTP on 0.0.0.0 port 8080 (http://0.0.0.0:8080/) ...
127.0.0.1 - - [22/Oct/2026 18:59:52] "GET / HTTP/1.1" 200 -
127.0.0.1 - - [22/Oct/2026 18:59:52] code 404, message File not found
127.0.0.1 - - [22/Oct/2026 18:59:52] "GET /nope HTTP/1.1" 404 -
```
Step 12 (real output; your timings will differ):
```
URL https://pypi.org/simple/ -> scheme=https host=pypi.org port=443
1. DNS   OK    pypi.org -> 151.101.128.223
2. TCP   OK    port 443 on 151.101.128.223 accepts connections
3. HTTP  status 200   (dns 0.001908s, connect 0.002225s, tls 0.217952s, first byte 0.273851s, total 0.512370s)
All good.
URL http://myapp.test:8080 -> scheme=http host=myapp.test port=8080
1. DNS   OK    myapp.test -> 127.0.0.1
2. TCP   OK    port 8080 on 127.0.0.1 accepts connections
3. HTTP  status 200   (dns 0.001253s, connect 0.001497s, tls 0.000000s, first byte 0.001973s, total 0.002031s)
All good.
URL http://localhost:9999 -> scheme=http host=localhost port=9999
1. DNS   OK    localhost -> 127.0.0.1
2. TCP   FAIL  cannot connect to 127.0.0.1 port 9999 (server down, wrong port, or a firewall)
exit code: 2
URL https://no-such-name.invalid -> scheme=https host=no-such-name.invalid port=443
1. DNS   FAIL  'no-such-name.invalid' does not resolve. Check spelling, /etc/hosts, and: dig no-such-name.invalid
exit code: 1
```
Step 13:
```
Checking lesson 23...
  PASS  something is listening on port 8080
  PASS  myapp.test resolves to 127.0.0.1 (thanks to /etc/hosts)
  PASS  http://myapp.test:8080/ answers 200 OK

Result: 3 passed, 0 failed.
```

## How it works
### 1. The path of one request
What happens when your code calls `https://pypi.org/simple/`:
```mermaid
flowchart LR
    A["your program<br/>(curl, browser, Python)"] --> B{"/etc/hosts<br/>has the name?"}
    B -- no --> C["DNS resolver<br/>(e.g. 8.8.8.8)"]
    B -- yes --> D
    C -- "pypi.org = 151.101.128.223" --> D["open TCP connection<br/>to 151.101.128.223:443"]
    D --> E["your router<br/>(default gateway)"]
    E --> F["internet routers<br/>(traceroute shows them)"]
    F --> G["server's firewall<br/>(is port 443 allowed?)"]
    G --> H["web server listening<br/>on port 443 (nginx)"]
    H --> I["TLS handshake,<br/>then HTTP request"]
    I --> J["response: 200 OK + page"]
```
| Step | Question | Tool that tests it | Typical failure message |
|---|---|---|---|
| 1. Name | does the name resolve? | `getent hosts NAME`, `dig NAME` | `Could not resolve host` |
| 2. Route | can packets get there? | `ping`, `traceroute` | `Network is unreachable` |
| 3. Port | is something listening and allowed? | `ss -tln` (on the server), `check-site.sh`, `nc -zv HOST PORT` | `Connection refused` / `timed out` |
| 4. TLS | is the certificate OK? | `curl -v https://...` | `SSL certificate problem` |
| 5. HTTP | what does the app answer? | `curl -i`, `curl -v` | `404`, `500`, `502 Bad Gateway` |

`check-site.sh` walks through steps 1, 3 and 5 in order and stops at the first failure with a different exit code for each (1, 2, 3).

### 2. IP addresses
- An **IPv4 address** is four numbers from 0 to 255: `151.101.128.223`. The `/16` in `172.17.0.3/16` says how many of the first bits name the network (here, the first two numbers): everything starting `172.17.` is on the same local network.
- **Special addresses**:

  | Address | Meaning |
  |---|---|
  | `127.0.0.1` (name: `localhost`) | **loopback**: "this same computer". Traffic never leaves the machine |
  | `0.0.0.0` (when listening) | "every network card of this computer" |
  | `10.x.x.x`, `172.16-31.x.x`, `192.168.x.x` | **private** ranges: home and company networks, cloud VPCs. Not reachable from the internet directly |
  | everything else | **public**: reachable on the internet |
  | `::1`, `fe80::...` | IPv6 versions (longer addresses with `:`). `::1` = loopback |
- Your laptop at home has a private address (`192.168.1.23`); your router has one public address and shares it (this is **NAT**). That is why `net-info.sh` shows a different "public IP".

### 3. Ports
A **port** (0-65535) says which program on a computer should get the traffic. Servers **listen** on a fixed port; clients use a random high port for their side.

| Port | Usually used by |
|---|---|
| 22 | SSH (lesson 24) |
| 53 | DNS |
| 80 / 443 | HTTP / HTTPS (websites, APIs) |
| 5432 | PostgreSQL |
| 6379 | Redis |
| 8000 / 8080 | development web servers (uvicorn, http.server) |
| 11434 | Ollama |

**Listening on `127.0.0.1` vs `0.0.0.0`**: `python3 -m http.server 8080 --bind 127.0.0.1` shows up in `ss` as `127.0.0.1:8080`: only programs on the same machine can connect. That is what you want for an app behind nginx (lesson 28). `0.0.0.0:8080` accepts connections from the whole network, so a firewall (lesson 26) should decide who gets in.

**TCP and UDP**: **TCP** is a phone call: a connection is set up, everything arrives in order, lost pieces are resent (web, SSH, databases). **UDP** is a postcard: fast, no connection, may get lost (DNS questions, video calls).

### 4. DNS and `/etc/hosts`
`dig pypi.org`, the parts that matter:
| Line | Meaning |
|---|---|
| `status: NOERROR` | the question was answered (`NXDOMAIN` = "no such name") |
| `QUESTION SECTION: pypi.org. IN A` | we asked for an **A record** (an IPv4 address); `AAAA` = IPv6, `CNAME` = "another name for", `MX` = mail server |
| `pypi.org. 10754 IN A 151.101.128.223` | the answer: name, **TTL** (seconds this answer may be cached), class, type, address. Several A records = several servers sharing the load |
| `SERVER: 8.8.8.8#53` | which DNS server answered, on port 53 |

`dig @1.1.1.1 pypi.org` asks a specific DNS server (here Cloudflare's), useful to tell "my DNS server is broken" from "the name is broken". `dig` talks to DNS only. `getent hosts` asks the system the way real programs do: `/etc/hosts` first, then DNS. That is why `myapp.test` worked in `curl` and `getent` but `dig myapp.test` finds nothing. The order is set in `/etc/nsswitch.conf` (`hosts: files dns`). DNS servers are listed in `/etc/resolv.conf` (on Ubuntu it points to a local helper, `127.0.0.53`; `resolvectl status` shows the real ones).

### 5. Reading `curl -v`
| Line starts with | Means | Example |
|---|---|---|
| `*` | curl telling you what it is doing | `* Connected to localhost (127.0.0.1) port 8080` |
| `>` | what **you sent** (the request) | `> GET / HTTP/1.1` = method, path, protocol version |
| `> Host:` | which website you want (one server can host many) | `> Host: localhost:8080` |
| `<` | what the **server sent back** (the response headers) | `< HTTP/1.0 200 OK` = the status line |
| (no prefix) | the body: the page itself | `<!doctype html>...` |

**Status codes** in one table: `2xx` success (`200 OK`, `201 Created`), `3xx` go elsewhere (`301`, `302`), `4xx` your request is wrong (`400`, `401` not logged in, `403` forbidden, `404` not found, `422` bad input, `429` too many requests), `5xx` the server failed (`500` crash, `502 Bad Gateway` = nginx could not reach the app behind it, `503` unavailable, `504` the app was too slow). For HTTPS, `curl -v` also shows the TLS handshake (`* SSL connection using TLSv1.3`, the certificate's `subject` and `expire date`).

### 6. `ping` and `traceroute`
`ping` sends small ICMP "echo" packets: `time=9.81 ms` is the round trip, `ttl=57` is how many more routers the reply could have passed, and `0% packet loss` is what you want. Many servers and cloud firewalls block ping, so **no reply does not prove the server is down**; a successful `curl` is the real test. `traceroute` sends packets that "die" after 1, 2, 3... routers, so each router on the path reports back: line 1 is usually your own router.

### 7. Inside `check-site.sh`
- `${url%%://*}`, `${rest#*://}`, `${hostport##*:}` are bash **parameter expansions** that cut text: `#` cuts from the left, `%` from the right, doubled (`##`, `%%`) means "as much as possible".
- `timeout 5 bash -c "exec 3<>/dev/tcp/$ip/$port"`: `/dev/tcp/HOST/PORT` is a bash feature (not a real file) that opens a TCP connection; `timeout 5` kills it after 5 seconds.
- `curl -w '%{http_code} %{time_namelookup} ...'` prints curl's own timing measurements; `read -r code t_dns ... <<< "$result"` splits them into variables (a here-string from lesson 20). A slow `tls` time points at the network; a slow `first byte` with fast `connect` points at the app (for an LLM API, the model thinking).

## If something goes wrong
- **`curl: (6) Could not resolve host`** → DNS problem. Check the spelling, then `getent hosts NAME`, then `dig NAME` and `dig @1.1.1.1 NAME`. If only the second works, your DNS server is the problem.
- **`curl: (7) Failed to connect ... Connection refused`** → you reached the computer, but nothing listens on that port. On the server: `ss -tln` to see the real port; the app may be down or on another port.
- **`Connection timed out`** (it hangs, then fails) → packets are dropped on the way, usually by a firewall (lesson 26) or a cloud security group, or the IP is wrong.
- **It works with `localhost` on the server but not from your laptop** → the app listens on `127.0.0.1` only (`ss -tln` shows `127.0.0.1:PORT`). Start it with `--host 0.0.0.0` (uvicorn) or `--bind 0.0.0.0`, and open the firewall. Or keep it private and use an SSH tunnel (lesson 24).
- **`sed: cannot rename /etc/sedXXXX: Device or resource busy`** in step 14 → you are in a Docker container, where `/etc/hosts` is mounted from outside. Use: `sudo sh -c 'grep -v myapp.test /etc/hosts > /tmp/hosts.new && cat /tmp/hosts.new > /etc/hosts'`.

## Try this
1. Run `dig +short github.com`, `dig +short AAAA google.com` and `dig +short MX gmail.com`. What kind of answer does each give?
2. Restart your server bound to loopback only (`python3 -m http.server 8080 --bind 127.0.0.1`) and compare the `ss -tln` line with before. Which other machines could reach it now?
3. Use `curl` to call a real JSON API and read the headers and the status code: `curl -i https://api.github.com/zen` (`-i` = include response headers). Then make it fail with a 404 by changing the path, and print only the status code.

<details><summary>Hints and solutions</summary>

1. github.com: one or more IPv4 addresses (A records). `AAAA` gives IPv6 addresses (with `:`). `MX` gives mail servers with a priority number, like `5 gmail-smtp-in.l.google.com.`.
2. The line becomes `127.0.0.1:8080` instead of `0.0.0.0:8080`. Now only programs on this computer can connect; other machines get "connection refused".
3. `curl -i https://api.github.com/zen` prints `HTTP/2 200`, headers like `content-type` and `x-ratelimit-remaining`, and a short sentence of wisdom. `curl -s -o /dev/null -w "%{http_code}\n" https://api.github.com/no-such-thing` prints `404`.
</details>

## Check yourself
1. In `http://myapp.test:8080/`, what does each part tell the computer?
2. `curl` says `Connection refused`. Is DNS the problem? What do you check next?
3. Your API works with `curl localhost:8000` on the server but not from your laptop. Name two possible reasons.
4. Why did `curl http://myapp.test:8080` work while `dig myapp.test` found nothing?

<details><summary>Answers</summary>

1. `http` = the protocol (and default port 80, overridden here); `myapp.test` = the name to look up (in `/etc/hosts` or DNS) to get an IP; `8080` = the port, i.e. which program on that computer; `/` = the path, which page to ask that program for.
2. No: refused means the name was resolved and the computer answered, but nothing listens on that port. Check on the server with `ss -tln` whether the app runs and on which port.
3. The app listens on `127.0.0.1` only, or a firewall / cloud security group blocks the port. (Also possible: you used the wrong IP.)
4. `curl` asks the system resolver, which reads `/etc/hosts` first. `dig` only asks DNS servers, which know nothing about your `/etc/hosts` line.
</details>

## Learn more (optional)
**Read the official docs**
- `ip(8)`: https://man7.org/linux/man-pages/man8/ip.8.html · `ss(8)`: https://man7.org/linux/man-pages/man8/ss.8.html
- `ping(8)`: https://man7.org/linux/man-pages/man8/ping.8.html · `hosts(5)`: https://man7.org/linux/man-pages/man5/hosts.5.html
- curl manual: https://curl.se/docs/manpage.html
- MDN, An overview of HTTP: https://developer.mozilla.org/en-US/docs/Web/HTTP/Overview
- MDN, HTTP response status codes: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status

**Watch**
- NetworkChuck, networking basics (IP addresses, DNS): https://www.youtube.com/results?search_query=networkchuck+what+is+an+ip+address
- freeCodeCamp, computer networking full course: https://www.youtube.com/results?search_query=freecodecamp+computer+networking+full+course
- Fireship, DNS in 100 seconds: https://www.youtube.com/results?search_query=fireship+dns+explained
- Hussein Nasser, how HTTP and TCP work: https://www.youtube.com/results?search_query=hussein+nasser+tcp+http+explained

## Next
→ [24 · SSH keys and remote servers](../24-ssh-keys-and-remote-servers)

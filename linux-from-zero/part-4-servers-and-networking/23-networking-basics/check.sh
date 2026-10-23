#!/usr/bin/env bash
# check.sh - checks lesson 23: your server is listening, myapp.test resolves, and HTTP works.
# Keep the python web server from step 7 running in another terminal, then:  ./check.sh

pass=0
fail=0
ok()  { echo "  PASS  $1"; pass=$((pass + 1)); }
bad() { echo "  FAIL  $1"; echo "        hint: $2"; fail=$((fail + 1)); }

echo "Checking lesson 23..."

# 1. Is something listening on TCP port 8080? ss -tln = TCP, listening, numbers; grep -q ':8080 ' = look for the port
if ss -tln | grep -q ':8080 '; then
  ok "something is listening on port 8080"
else
  bad "nothing is listening on port 8080" "start the server (Run it, step 7) and leave that terminal open"
fi

# 2. Does the name myapp.test point to this computer?
ip=$(getent hosts myapp.test | awk '{print $1; exit}')
if [[ "$ip" == "127.0.0.1" ]]; then
  ok "myapp.test resolves to 127.0.0.1 (thanks to /etc/hosts)"
else
  bad "myapp.test does not resolve to 127.0.0.1 (got '${ip:-nothing}')" "Run it, step 11: add the line to /etc/hosts"
fi

# 3. Does a real HTTP request by name work? -w '%{http_code}' prints only the status code
code=$(curl -s -o /dev/null -m 5 -w '%{http_code}' http://myapp.test:8080/)
if [[ "$code" == "200" ]]; then
  ok "http://myapp.test:8080/ answers 200 OK"
else
  bad "http://myapp.test:8080/ answered '$code'" "both checks above must pass first"
fi

echo ""
echo "Result: $pass passed, $fail failed."
if (( fail == 0 )); then
  echo "All done! Clean up: stop the server with Ctrl+C and run (step 14):"
  echo "  sudo sed -i '/myapp.test/d' /etc/hosts"
fi
(( fail == 0 ))

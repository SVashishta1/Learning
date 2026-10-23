#!/usr/bin/env bash
# setup.sh - creates a one-page website in ~/linux-practice/23/site to serve on port 8080.
# Run it with:  bash setup.sh

set -euo pipefail
site="$HOME/linux-practice/23/site"
mkdir -p "$site"

cat > "$site/index.html" <<'EOF'
<!doctype html>
<html>
  <head><meta charset="utf-8"><title>My tiny server</title></head>
  <body><h1>Hello from my own web server!</h1></body>
</html>
EOF

echo "Website ready in $site"
echo "Start it with:  cd $site && python3 -m http.server 8080"

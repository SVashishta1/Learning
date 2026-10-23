#!/usr/bin/env bash
# heredoc-demo.sh - "here documents": write many lines of text straight from a script.
# Run it with:  ./heredoc-demo.sh

set -euo pipefail
name="Sam"
out_dir="$HOME/linux-practice/20"
mkdir -p "$out_dir"

echo "== 1. <<EOF : variables and \$(...) ARE expanded =="
cat <<EOF
Hello $name, today is $(date +%A).
Your home is $HOME.
EOF
# ^ everything between <<EOF and the line that is exactly EOF is fed into cat.

echo ""
echo "== 2. <<'EOF' : quoted marker = text is kept EXACTLY (nothing expanded) =="
cat <<'EOF'
This is printed as-is: $name $(date) $HOME
Handy for writing scripts or config files that contain $ signs.
EOF

echo ""
echo "== 3. cat > file <<EOF : write a whole config file in one go =="
cat > "$out_dir/app.env" <<EOF
# created by heredoc-demo.sh on $(date +%F)
APP_NAME=ai-api
APP_PORT=8000
OWNER=$name
EOF
echo "Wrote $out_dir/app.env:"
cat "$out_dir/app.env"

echo ""
echo "== 4. <<< : a here-STRING feeds one line of text into a command =="
tr '[:lower:]' '[:upper:]' <<< "shout this please"   # tr = translate: every lowercase letter to uppercase

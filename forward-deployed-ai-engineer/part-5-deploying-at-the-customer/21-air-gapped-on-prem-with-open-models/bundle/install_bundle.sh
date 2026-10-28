#!/usr/bin/env bash
# install_bundle.sh: run on the AIR-GAPPED host, inside the copied bundle folder.  ./install_bundle.sh
# Verifies every file, loads the images, restores the models, and starts the stack. Never touches the internet.
set -euo pipefail
cd "$(dirname "$0")"

echo "1/4 verify checksums (a corrupted or tampered file stops the install)"
sha256sum --check --quiet SHA256SUMS && echo "    all files OK"

echo "2/4 load container images"
for tar in images/*.tar; do docker load -i "$tar"; done

echo "3/4 restore models (if the bundle has them)"
if [ -f models/ollama-models.tgz ]; then
  docker volume create offline-bundle_ollama-models >/dev/null
  # unpack with an image we already loaded (no internet to pull "alpine"); --user 0 because the volume belongs to root
  docker run --rm --user 0 -v offline-bundle_ollama-models:/data -v "$PWD/models":/in:ro \
    northwind/onprem-assistant:1.0.0 sh -c 'tar xzf /in/ollama-models.tgz -C /data'
  echo "    models restored"
fi

echo "4/4 start the stack"
if [ -f images/ollama.tar ]; then
  FAKE_LLM=0 docker compose -p offline-bundle --profile ollama up -d --no-build
else
  docker compose -p offline-bundle up -d --no-build
fi
docker compose -p offline-bundle ps
echo "Open http://$(hostname -I 2>/dev/null | awk '{print $1}'):8000  then run:"
echo "  docker compose -p offline-bundle exec assistant python verify_no_egress.py"

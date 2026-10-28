#!/usr/bin/env bash
# make_bundle.sh: run on a machine WITH internet. Packs everything the air-gapped site needs into one folder.
#
#   ./bundle/make_bundle.sh                          # FAKE-ready bundle: app + gateway images, wheels, source
#   WITH_OLLAMA=1 ./bundle/make_bundle.sh            # + the Ollama image and the models (several GB)
#
# Then copy the folder (USB disk, data diode, approved transfer) and run install_bundle.sh on the other side.
set -euo pipefail                                   # stop on any error, unset variable or failed pipe

HERE="$(cd "$(dirname "$0")/.." && pwd)"            # the lesson folder, wherever you run this from
OUT="${OUT:-$HERE/offline-bundle}"
APP_IMAGE="northwind/onprem-assistant:1.0.0"
GATEWAY_IMAGE="nginx:1.30-alpine"
OLLAMA_IMAGE="ollama/ollama:0.40.8"
MODELS="${MODELS:-qwen2.5:7b nomic-embed-text}"

mkdir -p "$OUT/images" "$OUT/wheels" "$OUT/models"

echo "1/5 build the app image"
if [ "${SKIP_BUILD:-0}" != "1" ]; then
  docker build -t "$APP_IMAGE" "$HERE"
fi

echo "2/5 save container images to .tar files"
docker image inspect "$GATEWAY_IMAGE" >/dev/null 2>&1 || docker pull "$GATEWAY_IMAGE"   # pull only if missing
docker save -o "$OUT/images/onprem-assistant.tar" "$APP_IMAGE"
docker save -o "$OUT/images/gateway.tar" "$GATEWAY_IMAGE"
if [ "${WITH_OLLAMA:-0}" = "1" ]; then
  docker image inspect "$OLLAMA_IMAGE" >/dev/null 2>&1 || docker pull "$OLLAMA_IMAGE"
  docker save -o "$OUT/images/ollama.tar" "$OLLAMA_IMAGE"
fi

echo "3/5 download Python wheels (for running without Docker, or rebuilding inside the site)"
pip download -r "$HERE/requirements.txt" -d "$OUT/wheels" \
  --only-binary=:all: --platform manylinux2014_x86_64 --python-version 3.12 --quiet

echo "4/5 download the models into a volume and pack it"
if [ "${WITH_OLLAMA:-0}" = "1" ]; then
  docker volume create bundle-ollama >/dev/null
  docker run -d --name bundle-ollama -v bundle-ollama:/root/.ollama "$OLLAMA_IMAGE" >/dev/null
  for m in $MODELS; do docker exec bundle-ollama ollama pull "$m"; done
  docker rm -f bundle-ollama >/dev/null
  docker run --rm -v bundle-ollama:/data -v "$OUT/models":/out alpine:3.20 tar czf /out/ollama-models.tgz -C /data .
  docker volume rm bundle-ollama >/dev/null
fi

echo "5/5 copy the deployment files and write checksums"
cp "$HERE/compose.yaml" "$HERE/requirements.txt" "$HERE/bundle/install_bundle.sh" "$OUT/"
mkdir -p "$OUT/gateway" && cp "$HERE/gateway/nginx.conf" "$OUT/gateway/"
(cd "$OUT" && find . -type f ! -name SHA256SUMS -print0 | sort -z | xargs -0 sha256sum > SHA256SUMS)
du -sh "$OUT"
echo "Bundle ready in $OUT"

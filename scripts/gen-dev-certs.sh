#!/usr/bin/env bash
# Generate self-signed TLS certificates for local HTTPS testing.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CERT_DIR="$ROOT/docker/certs"
mkdir -p "$CERT_DIR"

openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout "$CERT_DIR/privkey.pem" \
  -out "$CERT_DIR/fullchain.pem" \
  -subj "/CN=localhost/O=Knowledge Chatbot Dev/C=US"

echo "Wrote $CERT_DIR/fullchain.pem and $CERT_DIR/privkey.pem"

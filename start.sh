#!/usr/bin/env sh
set -eu

mkdir -p /run/secrets

# Decrypt secrets (expected mounts)
#   /secrets.enc/oauth.txt.enc
#   /secrets.enc/service-account.json.enc
#   /agekey.txt

if [ -f /secrets.enc/oauth.txt.enc ]; then
  sops --decrypt --age /agekey.txt /secrets.enc/oauth.txt.enc > /run/secrets/oauth.txt
  chmod 600 /run/secrets/oauth.txt
fi

if [ -f /secrets.enc/service-account.json.enc ]; then
  sops --decrypt --age /agekey.txt /secrets.enc/service-account.json.enc > /run/secrets/service-account.json
  chmod 600 /run/secrets/service-account.json
fi

exec python -m gam_mcp.server

#!/bin/bash
set -e
echo "Installing SOPS..."
SOPS_VERSION=$(curl -s "https://api.github.com/repos/getsops/sops/releases/latest" | jq -r .tag_name)
wget "https://github.com/getsops/sops/releases/download/${SOPS_VERSION}/sops-${SOPS_VERSION}.linux.amd64"
mv "sops-${SOPS_VERSION}.linux.amd64" /usr/local/bin/sops
chmod +x /usr/local/bin/sops
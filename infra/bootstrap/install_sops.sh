#!/bin/bash
set -e
echo "Installing SOPS..."
SOPS_VERSION="v3.12.2"
wget "https://github.com/getsops/sops/releases/download/${SOPS_VERSION}/sops-${SOPS_VERSION}.linux.amd64"
mv "sops-${SOPS_VERSION}.linux.amd64" /usr/local/bin/sops
chmod +x /usr/local/bin/sops
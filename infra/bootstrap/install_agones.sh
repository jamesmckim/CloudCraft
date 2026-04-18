#!/bin/bash
set -e
echo "Installing Agones via Helm..."
helm repo add agones https://agones.dev/chart/stable
helm repo update
helm upgrade my-release --install --namespace agones-system --create-namespace agones/agones
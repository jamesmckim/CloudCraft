#!/bin/bash
set -e

source /tmp/bootstrap/utils.sh

export KUBECONFIG=/ect/rancher/k3s/k3s.yaml

echo "Installing Agones via Helm..."
helm repo add agones https://agones.dev/chart/stable
helm repo update
helm upgrade my-release --install --namespace agones-system --create-namespace agones/agones

echo "Waiting for Agones core systems to come online..."
# The two main deployments Agones creates:
wait_for_deployment "agones-controller" "agones-system" "300s"
wait_for_deployment "agones-ping" "agones-system" "300s"

echo "Agones is fully operational!"
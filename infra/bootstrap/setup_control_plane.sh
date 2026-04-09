#!/bin/bash
set -e
exec > /var/log/cloudlab-setup.log 2>&1

# The token is passed as the first argument from profile.py
export CLUSTER_TOKEN=$1
REPO_DIR="/tmp/bootstrap"

echo "Installing base utilities..."
apt-get update
apt-get install -y curl wget apt-transport-https jq tar

echo "Running modular dependency installers..."
bash $REPO_DIR/install_age.sh
bash $REPO_DIR/install_sops.sh
bash $REPO_DIR/install_skaffold.sh
bash $REPO_DIR/install_helm.sh

echo "Spinning up Kubernetes (K3s Control Plane)..."
curl -sfL https://get.k3s.io | K3S_TOKEN="$CLUSTER_TOKEN" sh -s - server --cluster-init

# Set up kubeconfig so the root user can use kubectl and helm
export KUBECONFIG=/etc/rancher/k3s/k3s.yaml
chmod 644 /etc/rancher/k3s/k3s.yaml

echo "Waiting for K3s API to become ready..."
until [ -f /etc/rancher/k3s/k3s.yaml ] && kubectl get nodes &> /dev/null; do
    echo "Waiting for Kubernetes to initialize..."
    sleep 3
done

echo "Kubernetes is ready. Running Agones installer..."
bash $REPO_DIR/install_agones.sh

echo "Control Plane Setup Complete!"
touch /local/setup_complete
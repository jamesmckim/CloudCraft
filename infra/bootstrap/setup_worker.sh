#!/bin/bash
set -e
exec > /var/log/cloudlab-setup.log 2>&1

export CLUSTER_TOKEN=$1

apt-get update
apt-get install -y netcat-openbsd curl

echo "Waiting for Control Plane (node-0) to open port 6443..."
until nc -z node-0 6443; do
    echo "Waiting..."
    sleep 5
done

echo "Control plane is up! Joining the cluster..."
curl -sfL https://get.k3s.io | K3S_URL=https://node-0:6443 K3S_TOKEN="$CLUSTER_TOKEN" sh -

echo "Worker Setup Complete!"
touch /local/setup_complete
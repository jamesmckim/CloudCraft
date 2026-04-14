#!/bin/bash
set -e
# exec > /var/log/cloudlab-setup.log 2>&1

export CLUSTER_TOKEN=$1
export MASTER_IP=$2

apt-get update
apt-get install -y netcat-openbsd curl

echo "Waiting for Control Plane ($MASTER_IP) to open port 6443..."
until nc -z $MASTER_IP 6443; do
    echo "Waiting..."
    sleep 5
done

echo "Control plane is up! Joining the cluster..."
curl -sfL https://get.k3s.io | K3S_URL=https://$MASTER_IP:6443 K3S_TOKEN="$CLUSTER_TOKEN" sh -

echo "Worker Setup Complete!"
touch /tmp/setup_complete
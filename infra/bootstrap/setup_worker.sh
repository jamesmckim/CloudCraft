#!/bin/bash
set -e
# exec > /var/log/cloudlab-setup.log 2>&1

export CLUSTER_TOKEN=$1
export MASTER_IP=$2
export WORKER_IP=$3

if [[ "$MASTER_IP" == *":"* ]]; then
	SAFE_MASTER_IP="[${MASTER_IP}]"
else
	SAFE_MASTER_IP="${MASTER_IP}"
fi

apt-get update
apt-get install -y curl

echo "Waiting for Control Plane ($MASTER_IP) to open port 6443..."
until curl -k -s https://${SAFE_MASTER_IP}:6443 > /dev/null 2>&1; do
    echo "Waiting..."
    sleep 5
done

echo "Control plane is up! Joining the cluster..."
curl -sfL https://get.k3s.io | K3S_URL=https://${SAFE_MASTER_IP}:6443 K3S_TOKEN="$CLUSTER_TOKEN" sh -s - --node-ip="$WORKER_IP"

echo "Worker Setup Complete!"
touch /tmp/setup_complete
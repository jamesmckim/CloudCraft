#!/bin/bash
set -e

echo "=========================================="
echo "🚀 INITIATING FULL PLATFORM DEPLOYMENT..."
echo "=========================================="

echo "➡️  LAYER 1: Provisioning Infrastructure on NSF FABRIC..."
python provision_fabric.py

echo "➡️  LAYER 2: Configuring Kubernetes (K3s)..."
ansible/ansible-playbook site.yml --ask-vault-pass

echo "=========================================="
echo "✅ DEPLOYMENT COMPLETE!"
echo "Your platform is now live."
echo "=========================================="
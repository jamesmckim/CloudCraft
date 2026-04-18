#!/bin/bash
set -e
echo "Installing Age..."
AGE_VERSION="v1.3.1"
wget "https://github.com/FiloSottile/age/releases/download/${AGE_VERSION}/age-${AGE_VERSION}-linux-amd64.tar.gz"
tar -xzf "age-${AGE_VERSION}-linux-amd64.tar.gz"
mv age/age age/age-keygen /usr/local/bin/
rm -rf age age-*
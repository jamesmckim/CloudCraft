#!/bin/bash
set -e
echo "Installing Age..."
AGE_VERSION="v1.3.1"
curl -Lo age.tar.gz "https://github.com/FiloSottile/age/releases/download/${AGE_VERSION}/age-${AGE_VERSION}-linux-amd64.tar.gz"
tar -xzf age.tar.gz
mv age/age age/age-keygen /usr/local/bin/
rm -rf age-tar.gz age/
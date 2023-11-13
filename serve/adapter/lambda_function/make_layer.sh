#!/bin/sh

# ./make_layer.sh python-auth-tools arm64 arm64 "Layer of the dependencies for python-auth-tools"
# ./make_layer.sh python-auth-tools amd64 x86_64 "Layer of the dependencies for python-auth-tools"
# You'll need to install docker.io and qemu-user-static on Debian systems

set -e

NAME=$1
DOCKER_ARCH=$2
LAYER_ARCH=$2
DESCRIPTION=$3

sudo echo 'Running with sudo powers ...'

# See https://repost.aws/knowledge-center/lambda-layer-simulated-docker
echo 'Cleaning up in preparation ...'
sudo rm -f "tmp/${NAME}.zip"
sudo rm -rf tmp/python
mkdir -p tmp/python
echo 'Installing libraries using docker container ...'
sudo DOCKER_DEFAULT_PLATFORM="linux/${DOCKER_ARCH}" docker run -v "${PWD}:/var/task" "public.ecr.aws/sam/build-python3.11" /bin/sh -c "pip install -r requirements.txt -t tmp/python/lib/python3.11/site-packages/; exit"
echo "Zipping ..."
cd tmp
zip -r "${NAME}.zip" python
cd ..
echo "Publishing ..."
aws lambda publish-layer-version --compatible-architectures "${LAYER_ARCH}" --layer-name "${NAME}" --description "${DESCRIPTION}" --zip-file "fileb://tmp/${NAME}.zip" --compatible-runtimes "python3.11"
echo "done."

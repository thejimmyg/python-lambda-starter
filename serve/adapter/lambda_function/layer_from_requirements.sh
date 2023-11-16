#!/bin/sh

# You'll need to install docker.io and qemu-user-static on Debian systems
# rm -r ./tmp && ./serve/adapter/lambda_function/layer_from_requirements.sh "sudo -E docker" arm64|x86_64 '"boto3>1" openai xmlsec' python-auth-tools-arm64.zip "yum install libxml2-devel xmlsec1-devel xmlsec1-openssl-devel libtool-ltdl-devel"

set -e

DOCKER_CMD=$1
DOCKER_ARCH=$2
REQUIREMENTS=$3
ZIP_NAME=$4
CMD=$5

# See https://repost.aws/knowledge-center/lambda-layer-simulated-docker
mkdir -p tmp/python
echo "Installing $REQUIREMENTS using docker container ..."
DOCKER_DEFAULT_PLATFORM="linux/${DOCKER_ARCH}" $DOCKER_CMD run -e "REQUIREMENTS=$REQUIREMENTS" -v "${PWD}:/var/task" "public.ecr.aws/sam/build-python3.11" /bin/sh -c "echo $REQUIREMENTS; exit"
DOCKER_DEFAULT_PLATFORM="linux/${DOCKER_ARCH}" $DOCKER_CMD run -e "REQUIREMENTS=$REQUIREMENTS" -e "CMD=$CMD" -v "${PWD}:/var/task" "public.ecr.aws/sam/build-python3.11" /bin/sh -c "${CMD} ; pip install ${REQUIREMENTS} -t tmp/python/lib/python3.11/site-packages/; exit"
echo "Zipping ..."
cd tmp
zip -r layer.zip python
cd ..
mv tmp/layer.zip "${ZIP_NAME}"

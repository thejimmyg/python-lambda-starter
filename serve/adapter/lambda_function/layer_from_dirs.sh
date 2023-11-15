#!/bin/sh

# rm -r tmp; ./serve/adapter/lambda_function/layer_from_dirs.sh arm64|x86_64 'sudo -E docker' python-lambda-starter-arm64.zip

set -e

DOCKER_ARCH=$1
DOCKER_CMD=$2
ZIP_FILE=$3

# See https://repost.aws/knowledge-center/lambda-layer-simulated-docker
mkdir -p tmp/python
rsync -aHxv --exclude '**/__pycache__' serve tmp/python/
rsync -aHxv --exclude '**/__pycache__' kvstore tmp/python/
rsync -aHxv --exclude '**/__pycache__' tasks tmp/python/
find tmp/python -name '*.py' -print0 | xargs -0 echo 'Compiling '
DOCKER_DEFAULT_PLATFORM="linux/${DOCKER_ARCH}" $DOCKER_CMD run -v "${PWD}:/var/task" "public.ecr.aws/sam/build-python3.11" /bin/sh -c "find tmp/python -name '*.py' -print0 | xargs -0 xargs -0 python3 -m py_compile; exit"
echo 'done.'

cd tmp
zip -r starter.zip python
cd ..
mv tmp/starter.zip "$ZIP_FILE"

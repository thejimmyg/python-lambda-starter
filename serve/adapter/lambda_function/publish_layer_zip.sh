#!/bin/sh

# export AWS_REGION=us-east-1
# ./serve/adapter/lambda_function/publish_layer_zip.sh llm arm64|amd64 "Layer of the dependencies for python-auth-tools" python-auth-tools.zip
# You'll need to install the AWS CLI

set -e

NAME=$1
LAYER_ARCH=$2
DESCRIPTION=$3
ZIP_FILE=$4


echo "Publishing ..."
aws lambda publish-layer-version --compatible-architectures "${LAYER_ARCH}" --layer-name "${NAME}" --description "${DESCRIPTION}" --zip-file "fileb://${ZIP_FILE}" --compatible-runtimes "python3.11"
echo "done."




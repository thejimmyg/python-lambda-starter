# Python Lambda Starter

This is an extraction of the core ideas in [python-auth-tools](https://github.com/thejimmyg/python-auth-tools) but without any of the auth!

The intention is to merge both projects over time so that python-auth-tools can be deployed on Lambda or standalone.


## Principles

* Zero runtime dependencies -> low production maintenence, easier portability
* Implement only the subset of features you need -> faster cold starts, easier to deploy elsewhere, easier to learn, less to maintain
* Dynamic imports -> fast cold starts
* Be able to edit everything in the lambda code editor -> perfect for experiments or dire emergencies
* Rate limiting -> Never spend more than you expect


## Install

All platforms:

```sh
make venv
```

macOS:

```sh
brew install cfn-format awscli
```

Linux (you don't need the formatter to be able to build and deploy):

* https://github.com/awslabs/aws-cloudformation-template-formatter/releases/tag/v1.1.3
* https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html


## Dev

Build static files and typeddicts:

```sh
make
```

Clean up with:

```sh
make clean
```

Run code formatting for Python and CloudFormation:

```sh
make format
```

Static type checking and CloudFormation template validation:

```sh
make check
```

Unit tests:

```sh
make test
```


## Deploy

Follow [Deploy](deploy/README.md) for the pre-requisites.

Deploy the API Gateway version with:

```sh
export AWS_REGION="..."
export AWS_ACCESS_KEY_ID="..."
export AWS_SECRET_ACCESS_KEY="..."
export AWS_SESSION_TOKEN="..."
export CLOUDFORMATION_BUCKET="..."
export DOMAIN="..."
export HOSTED_ZONE_ID="..."
export PASSWORD="..."
export STACK_NAME="..."
make deploy-lambda
```

There are separate [deploy instructions for CloudFront](deploy/CLOUDFRONT.md), but you must also follow the [Deploy](deploy/README.md) pre-requisites first.


## License

Copyright 2023 James Gardner all rights reserved. License AGPLv3 except no scraping for the purposes of training AI models. Contributions in MIT please.

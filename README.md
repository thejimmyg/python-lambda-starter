# Python Lambda Starter

This is an extraction of the core ideas in [python-auth-tools](https://github.com/thejimmyg/python-auth-tools) but without any of the auth!

The intention is to merge both projects over time so that python-auth-tools can be deployed on Lambda or standalone.


## Principles

* Zero runtime dependencies -> low production maintenence, easier portability
* Implement only the subset of features you need -> faster cold starts, easier to deploy elsewhere, easier to learn, less to maintain
* Dynamic imports -> fast cold starts
* Be able to edit everything in the lambda code editor -> perfect for experiments or dire emergencies
* Rate limiting -> Never spend more than you expect

## Architecture

This uses the ports and adapters or hexagonal architecture with slightly
different nomlenclature to make it more accessible to those unfamiliar with the
style.

*Incoming* ports and adapters are called *adapters* and are in the `adapters`
folder. In each sub-folder the incoming port is in a file called `shared.py`
and the incoming adapters are in the other files.

*Outgoing* ports and adapters are called *drivers* and are in the `drivers`
folder. In each sub-folder the port is in `__init__.py` and the implementation in the other files.

Code that relies on a driver should import its implementation from `__init__.py`.
Within that file, the correct adapter will we chosen based on environment
variables.

Code that relies on environment variables should read them as late as possible,
and not assign them to global variables.


## Tasks

There is a simple system for running a series of sequential tasks, and tracking
their progress. The task system consists of a state machine to manage retries
(either errors, or because the lambda has reached the 15 min limit), an adapter
to connect the state machine to a lambda function, an `app.tasks` file with the
task definitions and a tasks driver to track task progress.

The tasks and HTTP lambdas both use exactly the same code, it is just deployed
to different lambda functions with different timeouts.


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

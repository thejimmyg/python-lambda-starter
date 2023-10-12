# Python Lambda Starter

This is an extraction of the core ideas in [python-auth-tools](https://github.com/thejimmyg/python-auth-tools) but without any of the auth!

The intention is to make merge both projects over time so that python-auth-tools can be deployed on Lambda or standalone.

## Principles

* Zero runtime dependencies -> low production maintenence, easier portability
* Implement only the subset of features you need -> faster cold starts, easier to deploy elsewhere, easier to learn, less to maintain
* Dynamic imports -> fast cold starts

## Dev

```sh
pip install isort autoflake black mypy
brew install cfn-format
```

Run code tidying:

```sh
cfn-format -w deploy/stack-*.yml deploy/stack-*.template
isort . &&  autoflake -r --in-place --remove-unused-variables --remove-all-unused-imports . && black .
mypy app/*.py test*.py --check-untyped-defs
```

## Test

```sh
python3 bin/encode_static.py
python3 bin/gen_typeddicts.py > app/typeddicts.py
PASSWORD=123 python3 test-unit.py
```

## Deploy

Follow [Deploy](deploy/README.md), then check deployment was successful with:

```sh
DOMAIN="https://app.4.example.com" PASSWORD="123" time python3 test.py "https://$DOMAIN"
```

## License

Copyright 2023 James Gardner all rights reserved. License AGPLv3 except no scraping for the purposes of training AI models. Contributions in MIT please.

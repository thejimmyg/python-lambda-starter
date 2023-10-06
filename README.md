# Python Lambda Starter

This is an extraction of the core ideas in [python-auth-tools](https://github.com/thejimmyg/python-auth-tools) but without any of the auth!

The intention is to make merge both projects over time so that python-auth-tools can be deployed on Lambda or standalone.

## Test

```sh
export URL="https://app.4.example.com"
python3 bin/encode_static.py
time python3 test.py "$URL"
```

## Dev

```sh
cfn-format -w deploy/stack-*.yml deploy/stack-*.template
isort . &&  autoflake -r --in-place --remove-unused-variables --remove-all-unused-imports . && black .
```

## License

Copyright 2023 James Gardner all rights reserved. License AGPLv3 except no scraping for the purposes of training AI models. Contributions in MIT please.

SRCS := $(shell find static -type f )
OBJS := $(SRCS:%=app/%.txt)


.PHONY: clean all test deploy check format deploy-lambda check-env venv deploy-check-env smoke serve smoke-local check-python

all: app/typeddicts.py $(OBJS)

app/static/%.txt: static/%
	mkdir -p app/static
	.venv/bin/python3 encode_static.py $< $@

app/typeddicts.py: gen_typeddicts.py openapi-*.json
	.venv/bin/python3 gen_typeddicts.py openapi-app.json > $@

venv:
	python3 -m venv .venv && .venv/bin/pip install isort autoflake black mypy cfn-lint boto3 boto3-stubs[stepfunctions] boto3-stubs[dynamodb]

deploy:
	@echo "Did you mean 'make deploy-lambda'?"

check-python:
	.venv/bin/mypy --check-untyped-defs .

check: app/typeddicts.py
	.venv/bin/cfn-lint \
	  stack-dns-zone.yml \
	  serve/adapter/lambda_function/cloudfront/stack-lambda-url.yml \
	  serve/adapter/lambda_function/cloudfront/stack-cloudfront.yml \
	  stack-cloudformation-bucket.yml \
	  serve/adapter/lambda_function/stack-certificate.yml \
	  serve/adapter/lambda_function/stack-api-gateway.yml \
	  serve/adapter/lambda_function/stack-api-gateway-domain.yml \
	  tasks/driver/stack-tasks-start.yml
	.venv/bin/cfn-lint -i W3002 -- \
	  serve/adapter/lambda_function/stack-lambda.yml \
	  tasks/adapter/lambda_function/stack-tasks.yml \
	  serve/adapter/lambda_function/cloudfront/stack-cloudfront.template \
	  stack-deploy-lambda.template

test: app/typeddicts.py $(OBJS)
	@echo 'Running kvstore tests ...'
	PYTHONPATH=$(PWD) PASSWORD=somepassword KVSTORE_DYNAMODB_TABLE_NAME=tasks TASKS_STATE_MACHINE_ARN=dummyarn AWS_REGION=test .venv/bin/python3 test/unit.py
	@echo 'done.'
	@echo 'Running openapi tests ...'
	DEV_MODE=true PYTHONPATH=$(PWD) PASSWORD=somepassword KVSTORE_DYNAMODB_TABLE_NAME=tasks TASKS_STATE_MACHINE_ARN=dummyarn AWS_REGION=test .venv/bin/python3 test/openapi.py
	@echo 'done.'
	@echo
	@echo "WARNING: Please to be sure to run 'DEV_MODE=true PASSWORD=123 make serve' and then in a different terminal run 'DEV_MODE=true PASSWORD=123 make smoke-local' to run the smoke tests ..."

format: format-python format-cfn

format-python:
	.venv/bin/autoflake -r --in-place --remove-unused-variables --remove-all-unused-imports . && .venv/bin/black .

format-cfn:
	cfn-format -w stack-* serve/adapter/lambda_function/stack-* serve/adapter/lambda_function/cloudfront/stack-* tasks/stack-*

serve:
ifndef PASSWORD
	$(error PASSWORD environment variable is undefined)
endif
	PYTHONPATH=. STORE_DIR=kvstore/driver .venv/bin/python3 serve/adapter/wsgi/bin/serve_wsgi.py

clean:
	rm -f app/static/*.txt app/typeddicts.py index.py
	rm -f lambda.zip tasks-lambda.zip
	rm -rf tmp kvstore/driver/driver_key_value_store
	find app serve tasks kvstore -type d  -name __pycache__ -print0 | xargs -0 rm -rf

tasks-lambda.zip:
	rm -rf tasks-lambda.zip
	cp tasks/adapter/lambda_function/index.py .
	zip \
	  --exclude '*/__pycache__/*' \
	  --exclude 'kvstore/driver/driver_key_value_store/*' \
	  --exclude 'kvstore/driver/sqlite.py' \
	  --exclude 'kvstore/driver/test.py' \
	  --exclude 'serve/' \
	  --exclude 'serve/**' \
	  --exclude 'tasks/*.yml' \
	  -r tasks-lambda.zip \
	  app tasks serve kvstore index.py template.py
	rm index.py

lambda.zip:
	rm -rf lambda.zip
	cp serve/adapter/lambda_function/index.py .
	zip \
	  --exclude '*/__pycache__/*' \
	  --exclude 'kvstore/driver/driver_key_value_store/*' \
	  --exclude 'kvstore/driver/sqlite.py' \
	  --exclude 'kvstore/driver/test.py' \
	  --exclude 'serve/adapter/lambda_function/*.md' \
	  --exclude 'serve/adapter/lambda_function/*.sh' \
	  --exclude 'serve/adapter/lambda_function/*.template' \
	  --exclude 'serve/adapter/lambda_function/*.yml' \
	  --exclude 'serve/adapter/lambda_function/cloudfront' \
	  --exclude 'serve/adapter/lambda_function/cloudfront/**' \
	  --exclude 'serve/adapter/lambda_function/index.py' \
	  --exclude 'serve/adapter/wsgi' \
	  --exclude 'serve/adapter/wsgi/*' \
	  --exclude 'tasks/*.yml' \
	  --exclude 'tasks/adapter' \
	  --exclude 'tasks/adapter/**' \
	  -r lambda.zip \
	  app tasks serve kvstore index.py template.py
	rm index.py

deploy-check-env-aws:
ifndef AWS_REGION
	$(error AWS_REGION environment variable is undefined)
endif
ifndef AWS_ACCESS_KEY_ID
	$(error AWS_ACCESS_KEY_ID environment variable is undefined)
endif
ifndef AWS_SECRET_ACCESS_KEY
	$(error AWS_SECRET_ACCESS_KEY environment variable is undefined)
endif
ifndef AWS_SESSION_TOKEN
	$(error AWS_SESSION_TOKEN environment variable is undefined)
endif


deploy-check-env: deploy-check-env-aws
ifndef DOMAIN
	$(error DOMAIN environment variable is undefined)
endif
ifndef CLOUDFORMATION_BUCKET
	$(error CLOUDFORMATION_BUCKET environment variable is undefined)
endif
ifndef HOSTED_ZONE_ID
	$(error HOSTED_ZONE_ID environment variable is undefined)
endif
ifndef STACK_NAME
	$(error STACK_NAME environment variable is undefined)
endif
ifndef PASSWORD
	$(error PASSWORD environment variable is undefined)
endif
deploy-lambda: deploy-check-env clean all check test lambda.zip tasks-lambda.zip
	@echo "Deploying stack $(STACK_NAME) for https://$(DOMAIN) to $(AWS_REGION) via S3 bucket $(CLOUDFORMATION_BUCKET) using Route53 zone $(HOSTED_ZONE_ID)" ...
	aws cloudformation package \
	    --template-file "stack-deploy-lambda.template" \
	    --s3-bucket "${CLOUDFORMATION_BUCKET}" \
	    --s3-prefix "${STACK_NAME}" \
	    --output-template-file "deploy-lambda.yml" && \
	aws cloudformation deploy \
	    --template-file "deploy-lambda.yml" \
	    --stack-name "${STACK_NAME}" \
	    --capabilities CAPABILITY_NAMED_IAM \
	    --disable-rollback \
	    --parameter-overrides \
	        "Domain=${DOMAIN}" \
	        "HostedZoneId=${HOSTED_ZONE_ID}" \
	        "ReservedConcurrency=-1" \
	        "ThrottlingRateLimit=50" \
	        "ThrottlingBurstLimit=200" \
	        "Password=${PASSWORD}" \
	        "Issuer=${ISSUER}" \
	        "Audiences=${AUDIENCES}"
	curl -v https://apps.jimmyg.org
	PYTHONPATH=. .venv/bin/python3 test/smoke.py "https://${DOMAIN}"


smoke:
ifndef DOMAIN
	$(error DOMAIN environment variable is undefined)
endif
ifndef PASSWORD
	$(error PASSWORD environment variable is undefined)
endif
	PYTHONPATH=. python3 test/smoke.py "https://${DOMAIN}"

smoke-local:
ifndef PASSWORD
	$(error PASSWORD environment variable is undefined)
endif
	PYTHONPATH=. python3 test/smoke.py "http://localhost:8000"


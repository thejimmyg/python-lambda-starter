SRCS := $(shell find static -type f )
OBJS := $(SRCS:%=app/%.txt)


.PHONY: clean all test deploy check format deploy-lambda check-env venv deploy-check-env smoke

all: app/typeddicts.py $(OBJS)

app/static/%.txt: static/%
	mkdir -p app/static
	.venv/bin/python3 bin/encode_static.py $< $@

app/typeddicts.py: bin/gen_typeddicts.py
	.venv/bin/python3 $< > $@

venv:
	python3 -m venv .venv && .venv/bin/pip install isort autoflake black mypy cfn-lint boto3 boto3-stubs[stepfunctions] boto3-stubs[dynamodb]

deploy:
	@echo "Did you mean 'make deploy-lambda'?"
check: app/typeddicts.py
	.venv/bin/cfn-lint deploy/stack-*.yml deploy/stack-*.template --ignore-templates deploy/stack-api-gateway.template deploy/stack-cloudfront.template deploy/stack-lambda.yml deploy/stack-tasks.yml
	.venv/bin/cfn-lint deploy/stack-api-gateway.template deploy/stack-cloudfront.template deploy/stack-lambda.yml deploy/stack-tasks.yml -i W3002
	.venv/bin/mypy app/*.py test/*.py --check-untyped-defs

test: app/typeddicts.py $(OBJS)
	PYTHONPATH=$(PWD) PASSWORD=somepassword TASKS_DYNAMODB_TABLE_NAME=tasks TASKS_STATE_MACHINE_ARN=dummyarn AWS_REGION=test .venv/bin/python3 test/unit.py

format: format-python format-cfn

format-python:
	.venv/bin/isort . && .venv/bin/autoflake -r --in-place --remove-unused-variables --remove-all-unused-imports . && .venv/bin/black .

format-cfn:
	cfn-format -w deploy/stack-*.yml deploy/stack-*.template

clean:
	rm -f app/static/*.txt app/typeddicts.py
	rm -f deploy/deploy*.yml
	rm -f lambda.zip tasks-lambda.zip
	find app adapter driver -type d  -name __pycache__ -print0 | xargs -0 rm -rf

tasks-lambda.zip: lambda.zip
	cp lambda.zip tasks-lambda.zip

lambda.zip:
	rm -rf lambda.zip
	zip --exclude '*/__pycache__/*' -r lambda.zip app adapter driver

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
	cd deploy && aws cloudformation package \
	    --template-file "stack-api-gateway.template" \
	    --s3-bucket "${CLOUDFORMATION_BUCKET}" \
	    --s3-prefix "${STACK_NAME}" \
	    --output-template-file "deploy-api-gateway.yml" && \
	aws cloudformation deploy \
	    --template-file "deploy-api-gateway.yml" \
	    --stack-name "${STACK_NAME}" \
	    --capabilities CAPABILITY_NAMED_IAM \
	    --parameter-overrides \
	        "Domain=${DOMAIN}" \
	        "HostedZoneId=${HOSTED_ZONE_ID}" \
	        "ReservedConcurrency=-1" \
	        "ThrottlingRateLimit=50" \
	        "ThrottlingBurstLimit=200" \
	        "Password=${PASSWORD}"
	.venv/bin/python3 test/smoke.py "https://${DOMAIN}"


smoke:
ifndef DOMAIN
	$(error DOMAIN environment variable is undefined)
endif
	python3 test/smoke.py "https://${DOMAIN}"


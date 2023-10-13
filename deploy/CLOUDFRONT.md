# CloudFront

The complexity here is that the certificate must be installed in `us-east-1` so you have to change your region to deploy it.

```
export ZONE_DOMAIN="4.example.com"
```

Let's do that standalone now:

```
export CLOUDFORMATION_BUCKET="app-cloudformation-23ba72m"
export DNS_ZONE_STACK_NAME="Dns"
export CERTIFICATE_STACK_NAME='Certificate'
export DOMAIN="app.${ZONE_DOMAIN}"
aws cloudformation describe-stacks --no-paginate --stack-name "${DNS_ZONE_STACK_NAME}" | python3 ../bin/stackout.py | python3 ../bin/json2env.py > dns-zone-output.env
source dns-zone-output.env
echo "${HOSTED_ZONE_ID}: ${NAMESERVER_RECORDS}"
```

```sh
time aws \
    --region us-east-1 \
    cloudformation deploy \
    --template-file "stack-certificate.yml" \
    --stack-name "${CERTIFICATE_STACK_NAME}" \
    --parameter-overrides \
        "Domain=${DOMAIN}" \
        "HostedZoneId=${HOSTED_ZONE_ID}"
```

Tip: You don't need to delete certificates from other regions to have them in `us-east-1`. You can have a certificate for the same domain in as many regions as you like.

Get the Certificae ARN:

```sh
aws --region=us-east-1 cloudformation describe-stacks --no-paginate --stack-name "${CERTIFICATE_STACK_NAME}" | python3 ../bin/stackout.py | python3 ../bin/json2env.py > certificate-output.env
source certificate-output.env
echo "${CERTIFICATE_ARN}"
```

Now to deploy the lambda and CloudFront.

Remove any `__pycache__` files that could interfere with the production environment.

Then you package everything into the CloudFormation bucket, then you deploy it. Let's do all steps together in this long command:

```
export STACK_NAME="App"
```

Package and deploy:

```sh
cd .. && python3 bin/encode_static.py && python3 bin/gen_typeddicts.py > app/typeddicts.py && cd deploy && rm -r ../app/__pycache__; \
aws cloudformation package \
    --template-file "stack-cloudfront.template" \
    --s3-bucket "${CLOUDFORMATION_BUCKET}" \
    --s3-prefix "${STACK_NAME}" \
    --output-template-file "deploy-cloudfront.yml" && \
time aws cloudformation deploy \
    --template-file "deploy-cloudfront.yml" \
    --stack-name "${STACK_NAME}" \
    --capabilities CAPABILITY_NAMED_IAM \
    --parameter-overrides \
        "Domain=${DOMAIN}" \
        "HostedZoneId=${HOSTED_ZONE_ID}" \
        "CertificateArn=${CERTIFICATE_ARN}" \
        "ReservedConcurrency=-1" \
        "Password=123"
```

Tips:
* The first time you run the `deploy` command add `--disable-rollback` just so that if anything goes wrong you don't need to wait for all the successful bits to be deleted before you can run the command again
* You'll need to delete the stack from the CloudFormation console if it rolls back before you can try to create it again
* If you need to re-deploy and it looks like the `package` command isn't picking up all your changes, run it again with `--s3-prefix` option changed to a different name to force re-uploading.

Then you can run the tests.

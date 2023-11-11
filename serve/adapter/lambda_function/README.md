# Deploy

WARNING: If you try to switch from a CloudFormation deloyment to an API Gateway one, it will fail with this error:

```
[Tried to create resource record set [name='app.4.james-at-fry.com.', type='A'] but it already exists]
```

CloudFormation isn't smart enough to make the change. You'll have to delete the recordset first.


## Helper Scripts

To run the deploy needs these helper scripts:

```sh
cat << EOF > json2env.py
import json
import shlex
import sys


def camel_to_snake(s):
    return "".join(["_" + c.lower() if c.isupper() else c for c in s]).lstrip("_")


def dict_to_shell(vars):
    output = ""
    for k, v in vars.items():
        if type(v) in [dict, list]:
            v = json.dumps(v)
        output += f"{camel_to_snake(k).upper()}={shlex.quote(str(v))}\n"
    return output


print(dict_to_shell(json.loads(sys.stdin.read() or "{}")), end="")
EOF
cat << EOF > stackout.py
import json
import sys


def filter_first_stack_outputs(stacks):
    return {
        o["OutputKey"]: o.get("OutputValue")
        for o in stacks["Stacks"][0].get("Outputs", [])
    }


print(json.dumps(filter_first_stack_outputs(json.loads(sys.stdin.read())), indent=2))
EOF
```

## Get Started


Set up your AWS credentials for the account and region you want to deploy to:

```
export AWS_REGION=eu-west-2
export AWS_ACCESS_KEY_ID="..."
export AWS_SECRET_ACCESS_KEY="..."
export AWS_SESSION_TOKEN="..."
```

## One Off Setup

### CloudFormation Bucket

You need an S3 bucket to deploy the lambda from:

```
export CLOUDFORMATION_BUCKET="app-cloudformation-jnba79"
export CLOUDFORMATION_BUCKET_STACK_NAME="AppCloudformationBucket"
```

Since bucket names are global to all accounts, you'll find that simple names
like cloudformation are already taken so you'll have to choose your own name. A
good strategy is to have a name that starts with something simple and ends with
a hypen and some random digits and lowercase letters. Bucket names also have to
be suitable to be used as subdomains in URLs.

Let's use CloudFormation itself to create the bucket that other CloudFormation
deployments will use.

The template is in bucket.yml so do take a look. It enables bucket versioning.

```sh
aws cloudformation create-stack \
  --template-body file://./stack-cloudformation-bucket.yml \
  --stack-name "${CLOUDFORMATION_BUCKET_STACK_NAME}" \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameters "ParameterKey=BucketName,ParameterValue=${CLOUDFORMATION_BUCKET}"
aws cloudformation wait stack-create-complete --stack-name "${CLOUDFORMATION_BUCKET_STACK_NAME}"
```

### Domain, DNS and Certificate

You'll also need a Route53 Hosted Zone ID. You can create one manually, or use DNS Delegation to set up a sub-domain.

First set up the subdomain in the AWS account you are deploying to so that you can find the nameservers you'll use.

In this example, the domain name is `4.example.com` and we want to use `app.4.example.com`.


```
export DNS_ZONE_STACK_NAME="Dns"
export ZONE_DOMAIN="4.example.com"
export DOMAIN="app.${ZONE_DOMAIN}"
```

Now deploy the hosted zone:

```sh
aws cloudformation create-stack \
    --template-body file://./stack-dns-zone.yml \
    --stack-name "${DNS_ZONE_STACK_NAME}" \
    --capabilities CAPABILITY_NAMED_IAM \
    --parameters "ParameterKey=Name,ParameterValue=${ZONE_DOMAIN}"
aws cloudformation wait stack-create-complete --stack-name "${DNS_ZONE_STACK_NAME}"
```

Get the Hosted Zone ID and Nameservers:

```sh
aws cloudformation describe-stacks --no-paginate --stack-name "${DNS_ZONE_STACK_NAME}" | python3 stackout.py | python3 json2env.py > dns-zone-output.env
source dns-zone-output.env
echo "${HOSTED_ZONE_ID}: ${NAMESERVER_RECORDS}"
```

Now you can set up your nameserver records however you like. If the parent part of the domain is in a different account, you can set an NS record using a CloudFormation template like this:

```
AWSTemplateFormatVersion: '2010-09-09'

Parameters:
  ParentHostedZoneId:
    Type: String
    MinLength: '1'
    Description: "Hosted Zone ID in which to add the records for delegation to a child AWS account"
  DomainName:
    Type: String
    MinLength: '1'
    Description: The domain you want the child AWS account to be able to use.  e.g. some.example.com
  ChildNameserverRecords:
    Type: String
    MinLength: '1'
    Description: The list of nameservers from the Hosted Zone that you have already created in the child AWS account

Resources:
  Route53RecordSet:
    Type: AWS::Route53::RecordSet
    Properties:
      Name: !Ref DomainName
      Type: NS
      TTL: 300
      HostedZoneId: !Ref ParentHostedZoneId
      ResourceRecords: !Split [ ' ', !Ref ChildNameserverRecords ]
```

Or you can add the data manually.


## Deploy/Upgrade

Now you have all the infrastructure to deploy your HTTP app.

API Gateway is a good option since it throttles too many requests without charge. It is a bad option in that it doesn't support HTTP at all, so if someone enters your domain into a browser, it will give a network error, not redirect to HTTPS (although Chrome seems to figure out to try HTTPS so perhaps Safari et al will follow suit at some point too).

CloudFront and a Lambda Function URL can work too, but you can't throttle CloudFront, it introduces caching and header stripping you might need to disable, and you have to be aware users can still access the Lambda Function URL directly and make sure that doesn't cause problems.

On the plus, bandwidth is about 10% cheaper than via API Gateway with per-request pricing similar, you can set up automatic gzip/brotli encoding, you can have failover into multiple regions and the EDGE network might deliver traffic faster to your users.

### API Gateway

Remove any `__pycache__` files that could interfere with the production environment.

Then you package everything into the CloudFormation bucket, then you deploy it. Let's do all steps together in this long command:

```
export STACK_NAME="App"
```

Package and deploy:

```sh
make deploy-lambda
```

Tips:
* The first time you run the `deploy` command add `--disable-rollback` just so that if anything goes wrong you don't need to wait for all the successful bits to be deleted before you can run the command again
* You'll need to delete the stack from the CloudFormation console if it rolls back before you can try to create it again
* If you need to re-deploy and it looks like the `package` command isn't picking up all your changes, run it again with `--s3-prefix` option changed to a different name to force re-uploading.

You may have to wait about another minute for certificates to work (`ssl.SSLCertVerificationError: [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: Hostname mismatch, certificate is not valid for 'app.4.example.com'. (_ssl.c:1006)`)

```sh
sleep 100
```

Then you can run the tests.

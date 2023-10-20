import os

import boto3

dynamodb = boto3.client(service_name="dynamodb", region_name=os.environ["AWS_REGION"])


def put(store, pk, data, sk="", ttl=None):
    assert "/" not in store
    actual_pk = f"{store}/{pk}"
    item = {
        "pk": {"S": actual_pk},
        "sk": {"S": "/" + sk},
    }
    if ttl:
        item["ttl"] = {"N": int(ttl)}
    item = data_to_dynamo_data(data)
    dynamodb.put_item(
        TableName=os.environ["KVSTORE_DYNAMODB_TABLE_NAME"],
        Item=item,
    )


def update(store, pk, data, sk="", ttl=None):
    assert "/" not in store
    actual_pk = f"{store}/{pk}"
    attribute_updates = data_to_dynamo_data(data, mode="update")
    if ttl:
        attribute_updates["ttl"] = {
            "Value": {"N": int(ttl)},
            "Action": "PUT",
        }
    dynamodb.update_item(
        TableName=os.environ["KVSTORE_DYNAMODB_TABLE_NAME"],
        Key={
            "pk": {"S": actual_pk},
            "sk": {"S": "/" + sk},
        },
        AttributeUpdates=attribute_updates,
    )


def delete(store, pk, sk=""):
    assert "/" not in store
    actual_pk = f"{store}/{pk}"
    dynamodb.delete_item(
        TableName=os.environ["KVSTORE_DYNAMODB_TABLE_NAME"],
        Key={
            "pk": {"S": actual_pk},
            "sk": {"S": "/" + sk},
        },
    )


def iterate(store, pk, sk_start="", limit=2, consistent=False):
    """
        https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Query.Pagination.html

        DynamoDB paginates the results from Query operations. With pagination, the Query results are divided into "pages" of data that are 1 MB in size (or less). An application can process the first page of results, then the second page, and so on.

    A single Query only returns a result set that fits within the 1 MB size limit. To determine whether there are more results, and to retrieve them one page at a time, applications should do the following:

        Examine the low-level Query result:

            If the result contains a LastEvaluatedKey element and it's non-null, proceed to step 2.

            If there is not a LastEvaluatedKey in the result, there are no more items to be retrieved.

        Construct a new Query request, with the same parameters as the previous one. However, this time, take the LastEvaluatedKey value from step 1 and use it as the ExclusiveStartKey parameter in the new Query request.

        Run the new Query request.

        Go to step 1.

    In other words, the LastEvaluatedKey from a Query response should be used as the ExclusiveStartKey for the next Query request. If there is not a LastEvaluatedKey element in a Query response, then you have retrieved the final page of results. If LastEvaluatedKey is not empty, it does not necessarily mean that there is more data in the result set. The only way to know when you have reached the end
    """
    assert "/" not in store
    actual_pk = f"{store}/{pk}"
    key_conditions = {
        "pk": {
            "ComparisonOperator": "EQ",
            "AttributeValueList": [{"S": actual_pk}],
        }
    }
    if sk:
        key_conditions["sk"] = {
            "ComparisonOperator": "GTE",
            "AttributeValueList": [{"S": "/" + sk_start}],
        }
    r = dynamodb.query(
        TableName=os.environ["KVSTORE_DYNAMODB_TABLE_NAME"],
        ConsistentRead=consistent,
        Limit=limit,
        KeyConditions=key_conditions,
    )
    sent = 0
    for item in r["Items"]:
        data = data_to_dynamo_data(item)
        parts = item["pk"]["S"].split("/")
        store = parts[0]
        pk = "/".join(parts[1:])
        sk = item["sk"]["S"]
        assert sk[0] == "/"
        sk = sk[1:]
        yield sk, data
        sent += 1
    r["LastEvaluateKey"]
    # while (not limit or sent < limit) and last_key:
    #     r = dynamodb.query(
    #         TableName=os.environ["KVSTORE_DYNAMODB_TABLE_NAME"],
    #         ConsistentRead=consistent,
    #         Limit=limit,
    #         KeyConditions=key_conditions,
    #         ExclusiveStartKey=last_key
    #     )
    #     last_key = r['LastEvaluateKey']


def data_to_dynamo_data(data, mode="normal"):
    assert mode in ["update", "normal"]
    assert "pk" not in data
    assert "sk" not in data
    assert "ttl" not in data
    result = {}
    for k in data:
        assert isinstance(k, str)
        if isinstance(data[k], int) or isinstance(data[k], float):
            value = {"N": data[k]}
        elif isinstance(data[k], str):
            value = {"S": data[k]}
        else:
            raise Exception(
                f"Value '{data[k]}' for key '{k}' is not a string or number"
            )
        if mode == "update":
            result[k] = {
                "Value": value,
                "Action": "PUT",
            }
        elif mode == "normal":
            result[k] = value
    return result
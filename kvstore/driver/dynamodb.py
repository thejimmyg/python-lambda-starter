import math
import os
import time
from typing import Any

import boto3

from .shared import NotFoundInStoreDriver, Remove

dynamodb = boto3.client(service_name="dynamodb", region_name=os.environ["AWS_REGION"])


def put(store, pk, data, sk="/", ttl=None):
    assert "/" not in store
    assert sk[0] == "/"
    if ttl is not None:
        assert isinstance(ttl, int), ttl
    actual_pk = f"{store}/{pk}"
    item = {
        "pk": {"S": actual_pk},
        "sk": {"S": sk},
    }
    if ttl:
        item["ttl"] = {"N": str(ttl)}
    item.update(_data_to_dynamo_format(data))
    dynamodb.put_item(
        TableName=os.environ["KVSTORE_DYNAMODB_TABLE_NAME"],
        Item=item,
    )


# https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Expressions.UpdateExpressions.html#Expressions.UpdateExpressions.Multiple
def _data_to_dynamo_update_format(data, ttl):
    assert "pk" not in data
    assert "sk" not in data
    assert "ttl" not in data
    # --update-expression "SET Price = Price - :p REMOVE InStock" \
    # --expression-attribute-values '{":p": {"N":"15"}}' \
    to_update = {}
    to_remove = []
    for k, v in data.items():
        assert isinstance(k, str)
        if v is Remove:
            to_remove.append(k)
        else:
            if isinstance(v, int) or isinstance(v, float):
                value = {"N": str(v)}
            elif isinstance(data[k], str):
                value = {"S": v}
            else:
                raise Exception(
                    f"Value {repr(data[k])} for key '{k}' is not a string or number"
                )
            to_update[k] = value
    if ttl is None:
        to_remove.append("ttl")
    elif ttl != "notchanged":
        to_update["ttl"] = {"N": str(ttl)}
    update_expression = ""
    expression_attribute_values = {}
    expression_attribute_names = {}
    if to_update:
        update_expression += (
            "SET " + ", ".join([f"#{k} = :{k}" for k in to_update]) + " "
        )
        for k in to_update:
            expression_attribute_values[":" + k] = to_update[k]
            expression_attribute_names["#" + k] = k
    if to_remove:
        update_expression += "REMOVE " + ", ".join(["#" + k for k in to_remove]) + " "
        for k in to_remove:
            expression_attribute_names["#" + k] = k
    return update_expression, expression_attribute_values, expression_attribute_names


def patch(store, pk, data, sk="/", ttl="notchanged"):
    assert "/" not in store
    assert sk[0] == "/"
    if ttl not in [None, "notchanged"]:
        assert isinstance(ttl, int), ttl
    actual_pk = f"{store}/{pk}"
    (
        update_expression,
        expression_attribute_values,
        expression_attribute_names,
    ) = _data_to_dynamo_update_format(data, ttl)
    args = dict(
        TableName=os.environ["KVSTORE_DYNAMODB_TABLE_NAME"],
        Key={
            "pk": {"S": actual_pk},
            "sk": {"S": sk},
        },
        UpdateExpression=update_expression,
    )
    if expression_attribute_values:
        args["ExpressionAttributeValues"] = expression_attribute_values
    if expression_attribute_names:
        args["ExpressionAttributeNames"] = expression_attribute_names
    dynamodb.update_item(**args)


def delete(store, pk, sk="/"):
    assert "/" not in store
    assert sk[0] == "/"
    actual_pk = f"{store}/{pk}"
    dynamodb.delete_item(
        TableName=os.environ["KVSTORE_DYNAMODB_TABLE_NAME"],
        Key={
            "pk": {"S": actual_pk},
            "sk": {"S": sk},
        },
    )


def iterate(
    store, pk, sk_start="/", limit=None, after=False, consistent=False
) -> tuple[Any, str | None]:
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
    assert sk_start[0] == "/"
    actual_pk = f"{store}/{pk}"

    if sk_start:
        # Should we be using ExclusiveStartKey here?
        # Shouldn't it be sk_start_after if a key is specified at all?
        if after:
            operator = ">"
        else:
            operator = ">="
        args = dict(
            TableName=os.environ["KVSTORE_DYNAMODB_TABLE_NAME"],
            ConsistentRead=consistent,
            KeyConditionExpression="(#pk = :pk) AND (#sk " + operator + " :sk)",
            ExpressionAttributeNames={
                "#pk": "pk",
                "#sk": "sk",
            },
            ExpressionAttributeValues={
                # WARNING: The values do not seem to be type checked currently.
                ":pk": {"S": actual_pk},
                ":sk": {"S": sk_start},
            },
        )
    else:
        args = dict(
            TableName=os.environ["KVSTORE_DYNAMODB_TABLE_NAME"],
            ConsistentRead=consistent,
            KeyConditionExpression="(#pk = :pk)",
            ExpressionAttributeNames={
                "#pk": "pk",
            },
            ExpressionAttributeValues={
                # WARNING: The value does not seem to be type checked currently.
                ":pk": {"S": actual_pk},
            },
        )
    if limit:
        args["Limit"] = limit
    # Need to add a filter expression for expired items. It could take days for DynamoDB to actually get around to expiring them
    args["FilterExpression"] = "#ttl > :ttl or attribute_not_exists(#ttl) "
    args["ExpressionAttributeNames"]["#ttl"] = "ttl"
    args["ExpressionAttributeValues"][":ttl"] = {"N": str(math.floor(time.time()))}
    r = dynamodb.query(**args)
    results = []
    for item in r["Items"]:
        parts = item["pk"]["S"].split("/")
        store = parts[0]
        pk = "/".join(parts[1:])
        sk = item["sk"]["S"]
        assert sk[0] == "/"
        # sk = sk[1:]
        del item["pk"]
        del item["sk"]
        ttl = None
        if "ttl" in item:
            ttl = int(item["ttl"]["N"])
            del item["ttl"]
        data = _data_from_dynamo_format(item)
        results.append((sk, data, ttl))
    if len(results) == 0 and not r.get("LastEvaluatedKey"):
        raise NotFoundInStoreDriver(f"No such pk '{pk}' in the '{store}' store")
    if len(results) == limit:
        return results, None
    else:
        return (
            results,
            # e.g.  {'pk': {'S': 'test/multiple'}, 'sk': {'S': '/2'}}
            "LastEvaluatedKey" in r and r["LastEvaluatedKey"]["sk"]["S"] or None,
        )


def _data_to_dynamo_format(data):
    assert "pk" not in data
    assert "sk" not in data
    assert "ttl" not in data
    result = {}
    for k in data:
        assert isinstance(k, str)
        if isinstance(data[k], int) or isinstance(data[k], float):
            value = {"N": str(data[k])}
        elif isinstance(data[k], str):
            value = {"S": data[k]}
        else:
            raise Exception(
                f"Value {repr(data[k])} for key '{k}' is not a string or number"
            )
        result[k] = value
    return result


def _data_from_dynamo_format(data):
    assert "pk" not in data
    assert "sk" not in data
    assert "ttl" not in data
    result = {}
    for k in data:
        assert isinstance(k, str)
        if "N" in data[k]:
            result[k] = float(data[k]["N"])
        elif "S" in data[k]:
            result[k] = data[k]["S"]
        else:
            raise Exception(
                f"Value {repr(data[k])} for key '{k}' cannot be converted to a string or number"
            )
    return result

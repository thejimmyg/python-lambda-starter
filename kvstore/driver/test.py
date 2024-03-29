# STORE_DIR=. PYTHONPATH=../../ python3 test.py
# AWS_REGION=eu-west-2 KVSTORE_DYNAMODB_TABLE_NAME=Apps-TaskStack-1SHSM43C3W9G0-Tasks PYTHONPATH=../../ python3 test.py

import math
import time

from kvstore.driver import delete, iterate, patch, put, NotFound, Remove, get

store = "test"


def main():
    # Choose a ttl with a floating point component
    ttl: float = float(math.floor(time.time()))
    if int(ttl) == ttl:
        ttl += 1.11234
    put(
        store=store,
        pk="foo-1",
        data={"hello": "world"},
        ttl=ttl,
    )

    for data, store_ in [
        (dict(pk="1"), store),
        (dict(sk="/hello"), store),
        (dict(ttl=1), store),
        (dict(ok="1"), "st/re"),
    ]:
        try:
            put(
                store=store_,
                pk="foo0",
                data=data,
            )
        except AssertionError:
            pass
        else:
            raise Exception(
                "Failed to trigger assertion error for put() with {data} and store {store_}"
            )
    for data in [
        (dict(pk="1"), store),
        (dict(sk="/hello"), store),
        (dict(ttl=1), store),
        (dict(ok="1"), "st/re"),
    ]:
        try:
            patch(
                store=store_,
                pk="foo0",
                data=data,
            )
        except AssertionError:
            pass
        else:
            raise Exception(
                "Failed to trigger assertion error for patch() with {data} and store {store_}"
            )
    try:
        put(
            store=store,
            pk="foo0",
            sk="doesnotstartwith/",
            data=dict(banana=3.14, foo="hello"),
        )
    except AssertionError:
        pass
    else:
        raise Exception(
            "Failed to trigger assertion error for put() with an sk that does not start with /"
        )
    try:
        patch(
            store=store,
            pk="foo0",
            sk="doesnotstartwith/",
            data=dict(banana=3.14, foo="hello"),
        )
    except AssertionError:
        pass
    else:
        raise Exception(
            "Failed to trigger assertion error for patch() with an sk that does not start with /"
        )

    try:
        put(
            store=store,
            pk="foo0",
            sk="/toobig",
            data=dict(large_key=("a" * 500 * 1024)),
        )
    except Exception:
        pass
    else:
        raise Exception(
            "Failed to trigger an error for put() with a payload that is too large"
        )
    put(
        store=store,
        pk="foo0",
        sk="/toobig",
        data=dict(large_key=("a" * 300 * 1024)),
    )
    try:
        patch(
            store=store,
            pk="foo0",
            sk="/toobig",
            data=dict(large_key_2=("a" * 300 * 1024)),
        )
    except Exception:
        pass
    else:
        raise Exception(
            "Failed to trigger an error for patch() with a payload that is now too large"
        )

    print("foo0 data checks passed")

    start_ttl = time.time() + 0.1
    put(
        store=store,
        pk="foo1",
        data=dict(banana=3.14, foo="hello"),
        ttl=start_ttl,
    )
    results, next_ = iterate(store=store, pk="foo1", consistent=True)
    assert len(results) == 1, results
    assert next_ is None
    sk, result, ttl = results[0]
    assert sk == "/", sk
    assert result == {"banana": 3.14, "foo": "hello"}, result
    assert ttl == start_ttl, (start_ttl, ttl)

    get_result, get_ttl = get(store=store, pk="foo1", sk="/", consistent=True)
    assert get_result == result, f"Results differ: {repr(result)}, {repr(get_result)}"
    assert get_ttl == ttl, f"TTLs differ: {repr(ttl)}, {repr(get_ttl)}"

    print("Stored foo1 successfully, get and iterate results are the same")

    start_ttl = time.time() + 0.1
    put(store=store, pk="foo1", data=dict(banana=3.15, foo="goodbye"), ttl=start_ttl)
    results, next_ = iterate(store=store, pk="foo1", consistent=True)
    assert len(results) == 1, results
    assert next_ is None
    sk, result, ttl = results[0]
    assert sk == "/", sk
    assert result == {"banana": 3.15, "foo": "goodbye"}, result
    assert ttl == start_ttl, ttl

    get_result, get_ttl = get(store=store, pk="foo1", sk="/", consistent=True)
    assert get_result == result, f"Results differ: {repr(result)}, {repr(get_result)}"
    assert get_ttl == ttl, f"TTLs differ: {repr(ttl)}, {repr(get_ttl)}"

    print("Updated foo1 successfully, get and iterate results are the same")

    put(
        store=store,
        pk="foo1",
        data=dict(banana=3.16, foo="bye"),
    )
    results, next_ = iterate(store=store, pk="foo1", consistent=True)
    assert len(results) == 1, results
    assert next_ is None
    sk, result, ttl = results[0]
    assert sk == "/", sk
    assert result == {"banana": 3.16, "foo": "bye"}, result
    assert ttl == None, ttl

    get_result, get_ttl = get(store=store, pk="foo1", sk="/", consistent=True)
    assert get_result == result, f"Results differ: {repr(result)}, {repr(get_result)}"
    assert get_ttl == ttl, f"TTLs differ: {repr(ttl)}, {repr(get_ttl)}"

    print(
        "Updated foo1 successfully without a ttl, get and iterate results are the same"
    )

    time.sleep(0.21)
    results, next_ = iterate(store=store, pk="foo1", consistent=True)
    assert len(results) == 1, results
    assert next_ is None
    sk, result, ttl = results[0]
    assert sk == "/", sk
    assert result == {"banana": 3.16, "foo": "bye"}, result
    assert ttl == None, ttl

    get_result, get_ttl = get(store=store, pk="foo1", sk="/", consistent=True)
    assert get_result == result, f"Results differ: {repr(result)}, {repr(get_result)}"
    assert get_ttl == ttl, f"TTLs differ: {repr(ttl)}, {repr(get_ttl)}"

    print(
        "foo1 is still there after the ttl time, now that no ttl has been set, get and iterate results are the same"
    )

    # Create an item
    put(
        store=store,
        pk="foo2",
        data=dict(banana=3.17, foo="hello"),
    )
    # Add a ttl, bar value and change banana
    start_ttl = time.time() + 0.1
    patch(
        store=store,
        pk="foo2",
        data=dict(banana=3.18, foo="hello", bar="bye"),
        ttl=start_ttl,
    )
    results, next_ = iterate(store=store, pk="foo2", consistent=True)
    assert len(results) == 1, results
    assert next_ is None
    sk, result, ttl = results[0]
    assert sk == "/", sk
    assert result == {"banana": 3.18, "foo": "hello", "bar": "bye"}, result
    assert ttl == start_ttl, ttl

    get_result, get_ttl = get(store=store, pk="foo2", sk="/", consistent=True)
    assert get_result == result, f"Results differ: {repr(result)}, {repr(get_result)}"
    assert get_ttl == ttl, f"TTLs differ: {repr(ttl)}, {repr(get_ttl)}"

    # Update the patch, changing the ttl
    start_ttl = time.time() + 0.2  # Has to be long enough to run these commands
    patch(
        store=store,
        pk="foo2",
        data=dict(banana=3.19, foo="hello", bar="bye"),
        ttl=start_ttl,
    )
    results, next_ = iterate(store=store, pk="foo2", consistent=True)
    assert len(results) == 1, results
    assert next_ is None
    sk, result, ttl = results[0]
    assert sk == "/", sk
    assert result == {"banana": 3.19, "foo": "hello", "bar": "bye"}, result
    assert ttl == start_ttl, ttl

    get_result, get_ttl = get(store=store, pk="foo2", sk="/", consistent=True)
    assert get_result == result, f"Results differ: {repr(result)}, {repr(get_result)}"
    assert get_ttl == ttl, f"TTLs differ: {repr(ttl)}, {repr(get_ttl)}"

    # Update the foo value, don't change the ttl
    patch(
        store=store,
        pk="foo2",
        data=dict(foo="hello1"),
    )
    results, next_ = iterate(store=store, pk="foo2", consistent=True)
    assert len(results) == 1, results
    assert next_ is None
    sk, result, ttl = results[0]
    assert sk == "/", sk
    assert result == {"banana": 3.19, "foo": "hello1", "bar": "bye"}, result
    assert ttl == start_ttl, ttl

    get_result, get_ttl = get(store=store, pk="foo2", sk="/", consistent=True)
    assert get_result == result, f"Results differ: {repr(result)}, {repr(get_result)}"
    assert get_ttl == ttl, f"TTLs differ: {repr(ttl)}, {repr(get_ttl)}"
    # Remove the ttl and bar value
    patch(
        store=store,
        pk="foo2",
        data=dict(banana=3.18, foo="hello", bar=Remove),
        ttl=None,
    )
    results, next_ = iterate(store=store, pk="foo2", consistent=True)
    assert len(results) == 1, results
    assert next_ is None
    sk, result, ttl = results[0]
    assert sk == "/", sk
    assert ttl == None, ttl
    assert result == {"banana": 3.18, "foo": "hello"}, result

    get_result, get_ttl = get(store=store, pk="foo2", sk="/", consistent=True)
    assert get_result == result, f"Results differ: {repr(result)}, {repr(get_result)}"
    assert get_ttl == ttl, f"TTLs differ: {repr(ttl)}, {repr(get_ttl)}"
    print("foo2 is successfully patched, get and iterate results the same")

    put(
        store=store,
        pk="foo3",
        data=dict(banana=3.14, foo="hello"),
        ttl=time.time() + 0.1,
    )
    time.sleep(1.1)
    try:
        print("===", iterate(store=store, pk="foo3", consistent=True))
    except NotFound:
        print("Cannot iterate foo3 since it has already expired")
    else:
        raise Exception("Showed the foo3 iterate result when it should have expired")
    try:
        print("===", get(store=store, pk="foo3", consistent=True))
    except NotFound:
        print("Cannot get foo3 since it has already expired")
    else:
        raise Exception("Showed the foo3 get result when it should have expired")

    put(store=store, pk="foo4", data=dict(banana=3.14, foo="hello"))
    delete(store=store, pk="foo4")
    try:
        print(iterate(store=store, pk="foo4", consistent=True))
    except NotFound:
        print("Cannot iterate foo4 since it has been successfully deleted")
    else:
        raise Exception(
            "Showed the foo4 iterate result when it should have been deleted"
        )

    try:
        print(get(store=store, pk="foo4", consistent=True))
    except NotFound:
        print("Cannot get foo4 since it has been successfully deleted")
    else:
        raise Exception("Showed the foo4 get result when it should have been deleted")

    # A large key forces the results to be returned in batches in the DynamoDB driver so that we can test next_
    # The size is chosen so that only two rows containing the large key can appear in one batch
    for i, large_key in enumerate(["1", "ab" * 199000]):
        # Now try multiple rows for the same pk:
        put(store=store, pk="multiple", data=dict(large_key=large_key, foo="multiple"))
        put(
            store=store,
            pk="multiple",
            data=dict(large_key=large_key, foo="multiple/2"),
            sk="/2",
        )
        put(
            store=store,
            pk="multiple",
            data=dict(large_key=large_key, foo="multiple/1"),
            sk="/1",
        )
        put(
            store=store,
            pk="multiple",
            data=dict(large_key=large_key, foo="multiple/3"),
            sk="/3",
        )

        results, next_ = iterate(store=store, pk="multiple", consistent=True)
        if i == 0:
            assert next_ is None, (next_, results[-1][0])
            assert results == [
                ("/", {"foo": "multiple", "large_key": large_key}, None),
                ("/1", {"foo": "multiple/1", "large_key": large_key}, None),
                ("/2", {"foo": "multiple/2", "large_key": large_key}, None),
                ("/3", {"foo": "multiple/3", "large_key": large_key}, None),
            ], results
        else:
            assert next_ == "/2", (next_, results[-1][0])
            # Note we are missing line 3
            assert results == [
                ("/", {"foo": "multiple", "large_key": large_key}, None),
                ("/1", {"foo": "multiple/1", "large_key": large_key}, None),
                ("/2", {"foo": "multiple/2", "large_key": large_key}, None),
            ], results
            # If we continue from the last key with after=True, we should get the remaining rows:
            next_results, next_next_ = iterate(
                store=store, pk="multiple", consistent=True, sk_start=next_, after=True
            )
            assert next_next_ == None, (next_next_, results[-1][0])
            assert next_results == [
                ("/3", {"foo": "multiple/3", "large_key": large_key}, None),
            ], (
                "Failed to get the remaining rows. First sk is: " + next_results[0][0]
            )

        results, next_ = iterate(store=store, pk="multiple", limit=2, consistent=True)
        assert next_ is None, (next_, results[-1][0])
        assert results == [
            ("/", {"foo": "multiple", "large_key": large_key}, None),
            ("/1", {"foo": "multiple/1", "large_key": large_key}, None),
        ], results

        results, next_ = iterate(
            store=store, pk="multiple", sk_start="/2", consistent=True
        )
        assert next_ is None, (next_, results[-1][0])
        assert results == [
            ("/2", {"foo": "multiple/2", "large_key": large_key}, None),
            ("/3", {"foo": "multiple/3", "large_key": large_key}, None),
        ], results

        results, next_ = iterate(
            store=store, pk="multiple", sk_start="/1", limit=2, consistent=True
        )
        assert next_ is None, (next_, results[-1][0])
        assert results == [
            ("/1", {"foo": "multiple/1", "large_key": large_key}, None),
            ("/2", {"foo": "multiple/2", "large_key": large_key}, None),
        ], results
        delete(store=store, pk="multiple")
        delete(store=store, pk="multiple", sk="/1")
        delete(store=store, pk="multiple", sk="/2")
        delete(store=store, pk="multiple", sk="/3")
        try:
            results, next_ = iterate(
                store=store, pk="multiple", sk_start="/1", limit=2, consistent=True
            )
        except NotFound:
            pass
        else:
            raise Exception(
                "Still got some of the multiple keys left after deleting them"
            )
        print(
            f"Iteration with multiple and {i==0 and 'small key' or 'large key'} working correctly"
        )

    put(
        store=store,
        pk="foo5",
    )
    assert ({}, None) == get(store=store, pk="foo5", consistent=True)
    results, next_ = iterate(store=store, pk="foo5", consistent=True)
    assert len(results) == 1, results
    assert next_ is None
    sk, result, ttl = results[0]
    assert sk == "/", sk
    assert result == {}, result
    assert ttl is None
    print("put foo5 key with no data, get and iterate behave correctly")


if __name__ == "__main__":
    main()

# CONFIG_STORE_DIR=. PYTHONPATH=../../ python3 test.py
# XXX What about putting/patching to add or remove a ttl?

import time

from kvstore.driver import delete, iterate, patch, put
from kvstore.driver.shared import NotFoundInStoreDriver


def main():
    start_ttl = time.time() + 0.1
    put(
        store="test",
        pk="foo1",
        data=dict(banana=3.14, foo="hello"),
        ttl=start_ttl,
    )
    results, next = iterate(store="test", pk="foo1")
    assert len(results) == 1, results
    assert next is None
    sk, result, ttl = results[0]
    assert sk == "/", sk
    assert result == {"banana": 3.14, "foo": "hello"}, result
    assert ttl == start_ttl, ttl
    print(__file__, "Stored foo1 successfully")

    start_ttl = time.time() + 0.1
    put(store="test", pk="foo1", data=dict(banana=3.15, foo="goodbye"), ttl=start_ttl)
    results, next = iterate(store="test", pk="foo1")
    assert len(results) == 1, results
    assert next is None
    sk, result, ttl = results[0]
    assert sk == "/", sk
    assert result == {"banana": 3.15, "foo": "goodbye"}, result
    assert ttl == start_ttl, ttl
    print(__file__, "Updated foo1 successfully")

    put(
        store="test",
        pk="foo1",
        data=dict(banana=3.16, foo="bye"),
    )
    results, next = iterate(store="test", pk="foo1")
    assert len(results) == 1, results
    assert next is None
    sk, result, ttl = results[0]
    assert sk == "/", sk
    assert result == {"banana": 3.16, "foo": "bye"}, result
    assert ttl == None, ttl
    print(__file__, "Updated foo1 successfully without a ttl")

    time.sleep(0.11)
    results, next = iterate(store="test", pk="foo1")
    assert len(results) == 1, results
    assert next is None
    sk, result, ttl = results[0]
    assert sk == "/", sk
    assert result == {"banana": 3.16, "foo": "bye"}, result
    assert ttl == None, ttl
    print(__file__, "foo1 is still there after the ttl time")

    put(
        store="test",
        pk="foo2",
        data=dict(banana=3.17, foo="hello"),
    )
    start_ttl = time.time() + 0.2
    patch(
        store="test",
        pk="foo2",
        data=dict(banana=3.18, foo="hello", bar="bye"),
        ttl=start_ttl,
    )
    results, next = iterate(store="test", pk="foo2")
    assert len(results) == 1, results
    assert next is None
    sk, result, ttl = results[0]
    assert sk == "/", sk
    assert result == {"banana": 3.18, "foo": "hello", "bar": "bye"}, result
    assert ttl == start_ttl, ttl
    print(__file__, "foo2 is successfully patched")

    put(store="test", pk="foo3", data=dict(banana=3.14, foo="hello"), ttl=time.time())
    try:
        print(iterate(store="test", pk="foo3"))
    except NotFoundInStoreDriver:
        print(__file__, "Cannot print foo3 since it has already expired")
    else:
        raise Exception("Showed the foo3 result when it should have expired")

    put(store="test", pk="foo4", data=dict(banana=3.14, foo="hello"))
    delete(store="test", pk="foo4")
    try:
        print(iterate(store="test", pk="foo4"))
    except NotFoundInStoreDriver:
        print(__file__, "Cannot print foo4 since it has been successfully deleted")
    else:
        raise Exception("Showed the foo4 result when it should have expired")

    # Now try multiple rows for the same pk:
    put(store="test", pk="multiple", data=dict(foo="multiple"))
    put(store="test", pk="multiple", data=dict(foo="multiple/2"), sk="/2")
    put(store="test", pk="multiple", data=dict(foo="multiple/1"), sk="/1")
    put(store="test", pk="multiple", data=dict(foo="multiple/3"), sk="/3")

    results, next = iterate(store="test", pk="multiple")
    assert next is None
    assert results == [
        ("/", {"foo": "multiple"}, None),
        ("/1", {"foo": "multiple/1"}, None),
        ("/2", {"foo": "multiple/2"}, None),
        ("/3", {"foo": "multiple/3"}, None),
    ], results

    results, next = iterate(store="test", pk="multiple", limit=2)
    assert next is None
    assert results == [
        ("/", {"foo": "multiple"}, None),
        ("/1", {"foo": "multiple/1"}, None),
    ], results

    results, next = iterate(store="test", pk="multiple", sk_start="/2")
    assert next is None
    assert results == [
        ("/2", {"foo": "multiple/2"}, None),
        ("/3", {"foo": "multiple/3"}, None),
    ], results

    results, next = iterate(store="test", pk="multiple", sk_start="/1", limit=2)
    assert next is None
    assert results == [
        ("/1", {"foo": "multiple/1"}, None),
        ("/2", {"foo": "multiple/2"}, None),
    ], results
    print(__file__, "Iteration working correctly")


if __name__ == "__main__":
    main()

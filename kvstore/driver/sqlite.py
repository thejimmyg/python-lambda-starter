import json
import os
import sqlite3
import time
from threading import RLock
from typing import Any

from .shared import NotFound, Remove

config_store_dir = os.environ.get("STORE_DIR", ".")
config_driver_key_value_store_dir = os.path.join(
    config_store_dir, "driver_key_value_store"
)
os.makedirs(config_driver_key_value_store_dir, exist_ok=True)
config_driver_key_value_store_db_path = os.path.join(
    config_driver_key_value_store_dir, "sqlite.db"
)


# This might not be needed if we create a cursor within each function, but I don't know enough about the underlying implementation to be sure.
rlock = RLock()


def get_sqlite3_thread_safety():
    # Mape value from SQLite's THREADSAFE to Python's DBAPI 2.0
    # threadsafety attribute.
    sqlite_threadsafe2python_dbapi = {0: 0, 2: 1, 1: 3}
    conn = sqlite3.connect(":memory:")
    threadsafety = conn.execute(
        """
select * from pragma_compile_options
where compile_options like 'THREADSAFE=%'
"""
    ).fetchone()[0]
    conn.close()
    threadsafety_value = int(threadsafety.split("=")[1])
    return sqlite_threadsafe2python_dbapi[threadsafety_value]


if get_sqlite3_thread_safety() == 3:
    check_same_thread = False
else:
    check_same_thread = True


_conn = None
_cur = None


def init():
    global _conn
    global _cur
    with rlock:
        if not _conn or not _cur:
            # See https://ricardoanderegg.com/posts/python-sqlite-thread-safety/
            _conn = sqlite3.connect(
                config_driver_key_value_store_db_path,
                check_same_thread=check_same_thread,
            )
            _cur = _conn.cursor()
            _cur.execute(
                "create table if not exists store (store text, pk text, sk text, ttl real, data text NOT NULL, PRIMARY KEY (store, pk, sk));"
            )
            _cur.execute(
                "create index if not exists store_ttl on store (ttl) where ttl is not NULL;"
            )


def cleanup():
    with rlock:
        if _conn:
            _conn.close()


def put(store: str, pk: str, data=None, sk="/", ttl=None):
    if data is None:
        data = {}
    assert "pk" not in data
    assert "sk" not in data
    assert "ttl" not in data
    assert "/" not in store
    if ttl is not None:
        assert isinstance(ttl, (int, float)), ttl
    if _cur is None:
        init()
    assert _conn is not None, "Database not initilaized, no _conn object."
    assert _cur is not None, "Database not initilaized, no _cur object."
    assert sk[0] == "/"
    for k, v in data.items():
        assert type(k) is str, f"Expected key {repr(k)} to be a string"
        assert isinstance(
            v, (float, int, str)
        ), f"Expected key {repr(k)} value to be a float, int or str. It is: {repr(v)}."
    cols = ["store", "pk", "sk", "ttl", "data"]
    values = [store, pk, sk, ttl, json.dumps(dict(data))]
    size = len(store) + 1 + len(pk) + len(pk) + len(str(ttl or "")) + len(values[-1])
    if size > 400 * 1024:
        raise Exception("Item is too large")
    with rlock:
        sql = (
            "INSERT OR REPLACE INTO "
            + "store"
            + "("
            + (", ".join(cols))
            + ") VALUES ("
            + (", ".join(["?" for v in values]))
            + ")"
        )
        # helper_log(__file__, sql, values)
        _cur.execute(sql, values)
        # Since we need to make a commit anyway, cleanup exired items
        _cur.execute(
            "delete from store where ttl is not NULL AND ttl <= ?", (time.time(),)
        )
        _conn.commit()


def delete(store: str, pk: str, sk="/"):
    assert "/" not in store
    if _cur is None:
        init()
    assert _conn is not None, "Database not initilaized, no _conn object."
    assert _cur is not None, "Database not initilaized, no _cur object."
    assert sk[0] == "/"

    with rlock:
        sql = "DELETE FROM " + "store" + " WHERE store=? AND pk=?"
        # helper_log(__file__, sql, pk)
        _cur.execute(
            sql,
            (
                store,
                pk,
            ),
        )
        # Since we need to make a commit anyway, cleanup exired items
        _cur.execute(
            "delete from store where ttl is not NULL AND ttl <= ?", (time.time(),)
        )
        _conn.commit()


# consistent is ignored
def iterate(
    store, pk, sk_start="/", limit=None, after=False, consistent=False
) -> tuple[Any, str | None]:
    if _cur is None:
        init()
    assert _conn is not None, "Database not initilaized, no _conn object."
    assert _cur is not None, "Database not initilaized, no _cur object."
    assert sk_start[0] == "/"
    with rlock:
        # Only return unexpired items
        if after:
            operator = ">"
        else:
            operator = ">="
        sql = (
            "select data, pk, sk, ttl from store where store = ? AND pk = ? and sk "
            + operator
            + " ? AND (ttl is NULL OR ttl > ?)"
        )
        values = [store, pk, sk_start, time.time()]
        if limit:
            sql += " LIMIT ?"
            values.append(limit)
        _cur.execute(sql, values)
        rows = _cur.fetchall()
        # helper_log(__file__, len(rows), rows)
        if len(rows) == 0:
            raise NotFound(f"No such pk '{pk}' in the '{store}' store")
        results: list[tuple[str, dict[str, Any], int]] = []
        size = 0
        last_row = None
        for row in rows:
            result = json.loads(row[0])
            size += len(row[0])
            # print(size)
            # Why this value?
            if size > int(1.5 * 1024 * 1024):
                return results, last_row
            results.append((row[2], result, row[3]))
            last_row = row[2]
        return results, None


# consistent is ignored
def get(
    store, pk, sk="/", consistent=False
) -> tuple[dict[str, int | float | str], float | int | None]:
    if _cur is None:
        init()
    assert _conn is not None, "Database not initilaized, no _conn object."
    assert _cur is not None, "Database not initilaized, no _cur object."
    assert sk[0] == "/"
    with rlock:
        sql = "select data, ttl from store where store = ? AND pk = ? AND sk = ? AND (ttl is NULL OR ttl > ?)"
        values = [store, pk, sk, time.time()]
        _cur.execute(sql, values)
        rows = _cur.fetchall()
        # helper_log(__file__, len(rows), rows)
        if len(rows) == 0:
            raise NotFound(f"No such pk '{pk}' in the '{store}' store")
        data = json.loads(rows[0][0])
        ttl = rows[0][1]
        return data, ttl


def patch(store, pk, data, sk="/", ttl="notchanged"):
    assert "pk" not in data
    assert "sk" not in data
    assert "ttl" not in data
    assert "/" not in store
    assert sk[0] == "/"
    if ttl not in ["notchanged", None]:
        assert isinstance(ttl, (int, float)), ttl
    for k, v in data.items():
        assert type(k) is str, f"Expected key {repr(k)} to be a string"
        assert (
            isinstance(v, (float, int, str)) or v is Remove
        ), f"Expected key {repr(k)} value to be a float, int, str or kvstore.driver.Remove. It is: {repr(v)}."
    # XXX This should be safe without a transaction because of the RLock? Unless the same thread makes requests concurrently.
    current, next = iterate(store, pk, sk_start=sk, limit=1, consistent=False)
    assert next is None, next
    sk_, data_, ttl_ = current[0]
    assert sk_ == sk, sk_
    new_data = {}
    new_data.update(data_)
    for k, v in data.items():
        if v is Remove:
            if k in new_data:
                del new_data[k]
        else:
            new_data[k] = v
    if ttl == "notchanged":
        new_ttl = ttl_
    else:
        new_ttl = ttl
    assert new_ttl != "notchanged"
    put(store, pk, new_data, sk, new_ttl)

import os

if os.environ.get("KVSTORE_DYNAMODB_TABLE_NAME"):
    from .dynamodb import delete, iterate, patch, put
else:
    from .sqlite import delete, iterate, patch, put


__all__ = ["delete", "put", "patch", "iterate"]

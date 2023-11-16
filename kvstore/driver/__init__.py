import os

if os.environ.get("KVSTORE_DYNAMODB_TABLE_NAME"):
    from .dynamodb import delete, iterate, patch, put, NotFound
else:
    from .sqlite import delete, iterate, patch, put, NotFound
from .shared import Remove

__all__ = ["delete", "put", "patch", "iterate", "NotFound", "Remove"]

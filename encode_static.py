import base64
import mimetypes
import os
import sys


def encode(src, dst):
    assert os.path.abspath(os.path.normpath(src)) != os.path.abspath(
        os.path.normpath(dst)
    ), "The source and destination must be different"
    with open(os.path.join(src), "rb") as fp:
        with open(dst, "wb") as txt:
            (type, encoding) = mimetypes.guess_type(src)
            if type is None:
                type = "application/octet-stream"
            txt.write(type.encode("utf8") + b"\n")
            txt.write(base64.b64encode(fp.read()))


if __name__ == "__main__":
    src = sys.argv[1]
    dst = sys.argv[2]
    encode(src, dst)

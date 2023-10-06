import base64
import mimetypes
import os

dirname = "static"

for filename in os.listdir(dirname):
    path = os.path.join(dirname, filename)
    with open(path, "rb") as fp:
        with open("app/static_" + filename + ".txt", "wb") as py:
            (type, encoding) = mimetypes.guess_type(path)
            if type is None:
                type = "application/octet-stream"
            py.write(type.encode("utf8") + b"\n")
            py.write(base64.b64encode(fp.read()))

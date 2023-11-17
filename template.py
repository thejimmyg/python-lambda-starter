import html


class Html:
    def __init__(self, escaped_html):
        self._escaped_html = escaped_html

    def render(self):
        return self._escaped_html

    def __add__(self, other):
        other_type = type(other)
        if other_type is Html:
            self._escaped_html += other._escaped_html
        elif other_type is str:
            self._escaped_html += html.escape(other, quote=True)
        else:
            raise Exception(f"Unsupported type: {repr(other)}")
        return self

    def __iadd__(self, other):
        return self.__add__(other)

    __str__ = render


class Base:
    def __init__(self, title, body):
        self._title = title
        self._body = body

    def title(self):
        return self._title

    def body(self):
        return self._body

    def render(self):
        return (
            Html(
                """\
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="X-UA-Compatible" content="ie=edge">
    <title>"""
            )
            + self.title()
            + Html(
                """</title>
    <link rel="stylesheet" href="/static/style.css">
    <link rel="icon" href="/favicon.ico" type="image/x-icon">
  </head>
  <body>
"""
            )
            + self.body()
            + Html(
                """
    <script src="/static/script.js"></script>
  </body>
</html>"""
            )
        ).render()


if __name__ == "__main__":
    p = Html("1")
    p += Html("2")
    assert str(Html("0") + p + Html("3")) == "0123"

    actual = Base(title="Home", body="    <Body>").render()
    expected = """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="X-UA-Compatible" content="ie=edge">
    <title>Home</title>
    <link rel="stylesheet" href="/static/style.css">
    <link rel="icon" href="/favicon.ico" type="image/x-icon">
  </head>
  <body>
    &lt;Body&gt;
    <script src="/static/script.js"></script>
  </body>
</html>"""
    if actual != expected:
        actual_lines = actual.split("\n")
        for i, line in enumerate(expected.split("\n")):
            if line != actual_lines[i]:
                print("-", line)
                print("+", actual_lines[i])
        raise AssertionError("Unexpected result of rendering Home")

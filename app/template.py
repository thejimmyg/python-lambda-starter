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


def render(title, body):
    return (
        Html('<!DOCTYPE html>\n<html lang="en"><head><title>')
        + title
        + Html(
            '</title><meta name="viewport" content="width=device-width, initial-scale=1.0"><meta charset="UTF-8"></head><body><h1>'
        )
        + title
        + Html("</h1>")
        + body
        + Html("</body></html>")
    )


def render_home():
    body = Html("<ul>\n")
    for link, text in [
        ("/html", "HTML"),
        ("/str", "str"),
        ("/dict", "dict"),
        ("/bytes", "bytes"),
        ("/other", "Other (should raise error)"),
    ]:
        body += Html('<li><a href="') + link + Html('">') + text + Html("</a></li>\n")
    body += Html("</ul>\n")
    return render("Home", body)

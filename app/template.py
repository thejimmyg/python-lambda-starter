from template import Html, Base


class Main(Base):
    def __init__(self, title, main):
        super().__init__("Main - " + title, body=None)
        self._main = main

    def body(self):
        return (
            Html(
                """
<main>
"""
            )
            + self.main()
            + Html(
                """
</main>
"""
            )
        )

    def main(self):
        return self._main


class Test(Base):
    def __init__(self, title):
        super().__init__(title, body=None)

    def body(self):
        body = Html("    <main>\n      <h1>Home</h1>\n<ul>\n")
        for link, text in [
            ("/html", "HTML"),
            ("/str", "str"),
            ("/dict", "dict"),
            ("/bytes", "bytes"),
            ("/static/hello.png", "img"),
            ("/other", "Other (should raise error)"),
            ("/submit", "Submit"),
        ]:
            body += (
                Html('<li><a href="') + link + Html('">') + text + Html("</a></li>\n")
            )
        body += Html("</ul>\n    </main>")
        return body

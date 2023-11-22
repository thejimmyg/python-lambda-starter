import os

# Disable any environment variables to make sure we don't accidentally make AWS calls in testing
for k in os.environ:
    if k not in (
        "PASSWORD",
        "AWS_REGION",
        "KVSTORE_DYNAMODB_TABLE_NAME",
        "TASKS_STATE_MACHINE_ARN",
    ):
        del os.environ[k]


def test_template_render_home():
    from app.template import Test

    actual = Test("Home").render()
    expected = """\
<!DOCTYPE html>
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
    <main>
      <h1>Home</h1>
<ul>
<li><a href="/html">HTML</a></li>
<li><a href="/str">str</a></li>
<li><a href="/dict">dict</a></li>
<li><a href="/bytes">bytes</a></li>
<li><a href="/static/hello.png">img</a></li>
<li><a href="/other">Other (should raise error)</a></li>
<li><a href="/submit">Submit</a></li>
</ul>
    </main>
    <script src="/static/script.js"></script>
  </body>
</html>"""

    if actual != expected:
        print(expected)
        print(actual)
        actual_lines = actual.split("\n")
        for i, line in enumerate(expected.split("\n")):
            if i > len(actual_lines) - 1:
                print(">", actual_lines[i])
                break
            if line != actual_lines[i]:
                print("-", line)
                print("+", actual_lines[i])
                break
        raise AssertionError("Unexpected result of rendering Home")


def test_web_submit():
    from unittest.mock import patch

    with patch("tasks.driver.begin_workflow") as begin_workflow, patch(
        "tasks.driver.begin_state_machine"
    ) as begin_state_machine, patch("app.tasks.wait") as wait:
        begin_workflow.return_value = "123"

        from app.app import app
        from app.template import Base
        from serve.adapter.shared import Base64, Http, Request, RespondEarly, Response

        http = Http(
            request=Request(
                path="/submit",
                query="",
                headers={},
                method="get",
                body=b"",
                verified_claims=None,
            ),
            response=Response(
                status="200 OK",
                headers={},
                body=None,
                RespondEarly=RespondEarly,
                Base64=Base64,
            ),
            context=dict(uid="123"),
        )
        app(http)
        assert isinstance(http.response.body, Base)
        body = http.response.body.render()
        assert "<form" in body, body

        http = Http(
            request=Request(
                path="/submit",
                query="",
                headers={},
                method="post",
                body=b"password=" + os.environ["PASSWORD"].encode("utf8") + b"&id=1",
                verified_claims=None,
            ),
            response=Response(
                status="200 OK",
                headers={},
                body=None,
                RespondEarly=RespondEarly,
                Base64=Base64,
            ),
            context=dict(uid="123"),
        )
        app(http)
        assert isinstance(http.response.body, Base)
        body = http.response.body.render()
        assert "Success" in body, body


def test_types():
    from app.typeddicts import enforce_SubmitInputResponse

    # Invalid case
    try:
        r: dict = {}
        assert enforce_SubmitInputResponse(r)
    except (KeyError, AssertionError):
        pass
    else:
        raise Exception("Failed to raise assertion")
    # Valid case
    s: dict = {"workflow_id": "some_date/some_guid"}
    assert enforce_SubmitInputResponse(s)
    assert s["workflow_id"]


def test_api():
    from unittest.mock import patch

    with patch("tasks.driver.begin_workflow") as begin_workflow, patch(
        "tasks.driver.begin_state_machine"
    ) as begin_state_machine, patch("app.tasks.wait") as wait:
        begin_workflow.return_value = "123"

        import json

        from app import typeddicts
        from app.app import app
        from serve.adapter.shared import Base64, Http, Request, RespondEarly, Response

        http = Http(
            request=Request(
                path="/api/submit_input",
                query="",
                headers={
                    "authorization": "Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6InRlc3QifQ.eyJhdWQiOiJhcHBzIiwiZXhwIjoxNzAwMzM0NzYxLCJpYXQiOjE3MDAzMzQxNjEsImlzcyI6Imh0dHBzOi8vYXV0aC5hcHBzLmppbW15Zy5vcmciLCJzY29wZSI6InJlYWQgd3JpdGUiLCJzdWIiOiJqYW1lcyJ9.C4ubfwO956ZTGp6RswjQs_95ZLNCSs5_eeLymtFhubLjgGzAOg2zE-rfGbcKRYySPDkwnjUivd5bqVP4wvRJ4o7ONOc0q8219qSPAQxX9-XrZVK7NWZOPS6dQ_vyU2APWdIPnYfmZRh9rXZ60DkMaLTbrW0t8SHzG2DQ1MV63hjWnFMTMvLZ7UG8YfLy7TbYzoG7BCZtw-eS7ySzeVpD372IUPpCnsUa-m-3mjgj8GfTaDRSau6n50Jnly1L1HJ7_6Z_velpbWn50P3ePpiZC_xql5tw-BwpcQ3mZuk4wf1TXAHlO05oy1GHHIa9u1P-ukOpFmByr5XXxq3Fni0tcw"
                },
                method="post",
                body=json.dumps({"id": 123, "password": os.environ["PASSWORD"]}).encode(
                    "utf8"
                ),
                verified_claims={
                    "aud": "apps",
                    "exp": 1700334761,
                    "iat": 1700334161,
                    "iss": "https://auth.apps.example.com",
                    "scope": "read write",
                    "sub": "james",
                },
            ),
            response=Response(
                status="200 OK",
                headers={},
                body=None,
                RespondEarly=RespondEarly,
                Base64=Base64,
            ),
            context=dict(uid="123"),
        )

        app(http)
        assert (
            isinstance(http.response.body, dict)
            and typeddicts.is_SubmitInputResponse(http.response.body)
            and "workflow_id" in http.response.body
        ), http.response.body


if __name__ == "__main__":
    import os
    import sys

    test_types()
    print(".", end="")
    sys.stdout.flush()

    test_template_render_home()
    print(".", end="")
    sys.stdout.flush()

    test_web_submit()
    print(".", end="")
    sys.stdout.flush()

    test_api()
    print(".", end="")
    sys.stdout.flush()

    print("\nSUCCESS")

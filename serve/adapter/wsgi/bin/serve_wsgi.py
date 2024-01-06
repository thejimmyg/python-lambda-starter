from serve.adapter.wsgi.wsgi import start_server
import importlib
import sys

app_path = "app:app"
bind = ""
if len(sys.argv) > 1:
    app_path = sys.argv[1]
if len(sys.argv) > 2:
    bind = sys.argv[2]
host, port = bind.split(":")
app_module_path, app_name = app_path.split(":")
app_module = importlib.import_module(app_module_path)
app = getattr(app_module, app_name)


def main() -> None:
    start_server({"": app}, port=int(port), host=host)


if __name__ == "__main__":
    main()

from app.app import app
from serve.adapter.wsgi.wsgi import start_server


def main() -> None:
    start_server({"": app})


if __name__ == "__main__":
    main()

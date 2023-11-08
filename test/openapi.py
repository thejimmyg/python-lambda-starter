def test_submit_input() -> None:
    from app.typeddicts import SubmitInput, app_submit_input

    result = app_submit_input(
        "http://localhost:8000/api", SubmitInput(id=1, password="password")
    )
    assert result == {"success": True}, result


def main() -> None:
    import subprocess
    import sys
    import time

    process = subprocess.Popen([sys.executable, "test/openapi-server.py"])
    time.sleep(1)
    try:
        test_submit_input()
        print(".", end="")
    except Exception:
        print("\nFAILED\n")
        raise
    else:
        print("\nSUCCESS")
    finally:
        # Send a SIGTERM
        process.kill()


if __name__ == "__main__":
    main()

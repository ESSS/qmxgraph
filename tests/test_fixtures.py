import os

pytest_plugins = "pytester"


def test_port_fixture(testdir) -> None:
    """
    Listen on several ports to make sure that fixture `port` is able to get
    always a free port.
    """
    import shutil

    shutil.copy(os.path.join(os.path.dirname(__file__), "conftest.py"), str(testdir.tmpdir))

    testdir.makepyfile(
        test_port="""
        import pytest

        def test_port(port) -> None:
            port_ = port.get()

            import socket
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            with pytest.raises(socket.error):
                s.connect(('localhost', port_))
    """
    )
    result = testdir.runpytest()
    result.stdout.fnmatch_lines(["*1 passed*"])

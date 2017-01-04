import os
import sys
from contextlib import contextmanager


class CherryPyServer(object):
    """
    cherrypy is really practical to host a webpage. However it is one big
    drawback: it is mostly intended to run a single server per process, as it
    stores lots of its configuration in globals.

    This can be troublesome during tests when we may want to host many pages
    at same time (for instance, to test different initialization conditions).

    This class encapsulates and tries to hide these problems. Each
    cherrypy-hosted page is launched in an individual subprocess by `start`
    and this process can be killed by a `stop` call.
    """

    def __init__(self):
        self.server_pid = None

    def start(self, page, config):
        """
        Start a cherrypy server in individual process.

        :param object page: An object containing entry points exposed to
            cherrypy.
        :param dict config: A configuration compatible with cherrypy.
        """
        if self.is_running():
            return

        if not sys.platform.startswith('win'):
            signaled = []

            def handler(signum, frame):
                signaled.append(True)

            import signal
            signal.signal(signal.SIGCONT, handler)

        from multiprocessing import Process
        cherrypy_server = Process(
            target=_do_start_server, args=(os.getpid(), page, config))
        cherrypy_server.start()

        if not sys.platform.startswith('win'):
            timeout = current = 5
            step = 0.2
            import time
            address = '{}:{}'.format(
                config['global']['server.socket_host'],
                config['global']['server.socket_port'],
            )
            while not signaled:
                current -= step
                assert current > 0, "Server unable to start at {} after a " \
                                    "timeout of {} seconds".format(
                                        address, timeout)
                time.sleep(step)

        self.server_pid = cherrypy_server.pid

    def is_running(self):
        """
        :rtype: bool
        :return: If server is running.
        """
        return self.server_pid is not None

    def stop(self):
        """
        Kill process running cherrypy server.
        """
        if self.server_pid is not None:
            import signal
            try:
                os.kill(self.server_pid, signal.SIGTERM)
            except WindowsError as e:
                # If already dead for any reason, just let it go
                if e.winerror != 5:
                    exc_type, exc_value, tb = sys.exc_info()
                    import six
                    six.reraise(exc_type, exc_value, tb)
            if not sys.platform.startswith('win'):
                os.waitpid(self.server_pid, 0)

        self.server_pid = None

    @contextmanager
    def single_shot(self, page, config):
        """
        Starts a cherrypy server, yields and finally stops server in the end
        of context.

        :param object page: An object containing entry points exposed to
            cherrypy.
        :param dict config: A configuration compatible with cherrypy.
        """
        self.start(page, config)
        try:
            yield
        finally:
            self.stop()


# free function as member static functions aren't pickable and this must be
# stateless and pickable as it is called from other process
def _do_start_server(pid, page, config):
    import cherrypy

    if not sys.platform.startswith('win'):
        # 'main' event is more reliable than 'start' event, as 'start' is
        # fired just BEFORE server started, so it may not be necessarily be
        # ready for access yet. 'main' though is only fired during server
        # loop so it is already set up when reaches that point.
        channel = 'main'

        def callback():
            cherrypy.engine.unsubscribe(channel, callback)

            import os
            import signal
            os.kill(pid, signal.SIGCONT)

        cherrypy.engine.subscribe(channel, callback)

    cherrypy.quickstart(page, config=config)

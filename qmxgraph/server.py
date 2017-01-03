"""
Helper methods to serve a page with same graph drawing widget as the one
used embedded with QGraphWidget. Helpful to test graph widget features using
Selenium, for instance.
"""

from __future__ import absolute_import

import os
from contextlib import contextmanager

import cherrypy

from qmxgraph import deploy


def gen_config(port, mxgraph_path, own_path, stencils_path=None, debug=False):
    """
    :param int port: Port where graph page is going to be served.
    :param str mxgraph_path: Path in file system where mxGraph static files
        are located.
    :param str own_path: Path in file system where QmxGraph's own static
        files are located.
    :param str|None stencils_path: Path to folder in file system where
        stencil files are located, if any.
    :param bool debug: If enabled, enables configurations like logging that
        may help debugging issues.
    :rtype: dict
    :return: A configuration dict in format expected by CherryPy.
    """
    mxgraph_path = os.path.abspath(mxgraph_path)
    own_path = os.path.abspath(own_path)

    # NOTE: CherryPy doesn't know how to deal with str in its configuration
    # in Python 2.7.
    #
    # https://github.com/cherrypy/cherrypy/issues/1184
    config = {
        "global": {
            "server.socket_host": "0.0.0.0",
            "server.socket_port": port,
        },
        # Static content
        "/own": {
            "tools.staticdir.dir": portable_path(own_path),
            "tools.staticdir.on": True,
        },
        "/mxgraph": {
            "tools.staticdir.dir": portable_path(mxgraph_path),
            "tools.staticdir.on": True,
        },
    }

    if stencils_path:
        stencils_path = os.path.abspath(stencils_path)
        config.update({
            "/stencils": {
                "tools.staticdir.dir": portable_path(stencils_path),
                "tools.staticdir.on": True,
            },
        })

    if not debug:
        config["global"].update({
            # http://docs.cherrypy.org/en/latest/basics.html#disable-logging
            'log.screen': False,
        })

    # ALWAYS write logs about hosted server, using port to differentiate
    # between different instances/processes. This is really helpful when for
    # any reason server is unable to be started, for instance.
    log_path = os.path.dirname(__file__)
    config["global"].update({
        'log.access_file':
            '{}/.server_logs/cherrypy_port{}_access.log'.format(
                log_path, port),
        'log.error_file':
            '{}/.server_logs/cherrypy_port{}_error.log'.format(
                log_path, port),
    })

    return config


class GraphPage(object):
    """
    A simple page showing a graph drawing widget using mxGraph as its backend.
    """

    def __init__(
            self, template_path, options=None, styles=None, stencils=tuple()):
        """
        :param str template_path: Path where graph HTML templates are
            located.
        :param GraphOptions options: Options of graph drawing widget,
            uses default if not given.
        :param GraphStyles styles: Styles available in graph drawing
            widget, uses default if not given.
        :param iterable[str] stencils: Stencils available in graph drawing
            widget.
        """
        self.template_path = template_path

        from qmxgraph.configuration import GraphStyles
        from qmxgraph.configuration import GraphOptions

        if options is None:
            options = GraphOptions()

        if styles is None:
            styles = GraphStyles()

        self.options = options
        self.styles = styles
        self.stencils = stencils

    @cherrypy.expose
    def index(self, *args, **kwargs):
        """
        :rtype: str
        :return: Entry point of graph page, returns HTML that contain graph
            drawing widget.
        """
        from qmxgraph import render
        html = render.render_hosted_html(
            options=self.options,
            styles=self.styles,
            stencils=self.stencils,
            # Environment of mxGraph static files is served together with
            # page (see config generation in this module)
            mxgraph_path='mxgraph',
            own_path='own',
            template_path=self.template_path,
        )
        return html


@contextmanager
def host(port, options=None, styles=None, stencils=tuple()):
    """
    Hosts a server with graph drawing page then stops it once context is
    over.

    :param int port: Port where graph page is going to be served.
    :param GraphOptions options: Options of graph drawing widget.
    :param GraphStyles styles: Styles available in graph drawing widget.
    :param iterable[str] stencils: Sequence of paths in file system
        referring to stencil files.
    """
    mxgraph_path = os.path.join(
        deploy.get_conda_env_path(), 'mxgraph', 'javascript', 'src')
    own_path = os.path.join(os.path.dirname(__file__), 'page')

    stencils_path = None
    stencils_ = []
    for stencil in stencils:
        candidate = os.path.dirname(stencil)
        assert candidate != stencils_path, "Due to simplification, expects " \
                                           "all stencils in same folder"
        stencils_path = candidate
        stencils_.append('stencils/{}'.format(os.path.basename(stencil)))

    config = gen_config(
        port=port,
        mxgraph_path=mxgraph_path,
        own_path=own_path,
        stencils_path=stencils_path,
        debug=False,
    )

    page = GraphPage(
        template_path=own_path, options=options,
        styles=styles, stencils=stencils_)

    from ._cherrypy_server import CherryPyServer
    cherrypy_server = CherryPyServer()
    with cherrypy_server.single_shot(page=page, config=config):
        yield Host(
            address='http://localhost:{}'.format(
                config['global']['server.socket_port']),
            options=page.options,
            styles=page.styles,
            stencils=stencils_,
        )


class Host(object):
    """
    Object containing details about graph drawing page currently hosted.
    """

    def __init__(self, address, options, styles, stencils):
        self._address = address
        self._options = options
        self._styles = styles
        self._stencils = stencils

    @property
    def address(self):
        return self._address

    @property
    def options(self):
        return self._options

    @property
    def styles(self):
        return self._styles

    @property
    def stencils(self):
        return self._stencils


def portable_path(path):
    """
    :param str path: A file path.
    :rtype: str
    :return: File path always using slash (/) as path separator, in all
        platforms.
    """
    import sys
    if sys.platform.startswith('win'):
        path = path.replace('\\', '/')
    return path


if __name__ == '__main__':
    mxgraph_path = os.path.join(
        deploy.get_conda_env_path(), 'mxgraph', 'javascript', 'src')
    own_path = os.path.join(os.path.dirname(__file__), 'page')

    config = gen_config(
        port=60066,
        mxgraph_path=mxgraph_path,
        own_path=own_path,
        debug=True,
    )
    cherrypy.quickstart(GraphPage(template_path=own_path), config=config)

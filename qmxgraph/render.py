import json


def render_embedded_html(options, styles, stencils, mxgraph_path, own_path):
    """
    Renders an HTML that is able to load graph drawing widget page embedded
    in a Qt widget.

    :param GraphOptions options: Options of graph drawing widget.
    :param GraphStyles styles: Styles available in graph drawing widget.
    :param iterable[str] stencils: Stencils available in graph drawing
        widget.
    :param str mxgraph_path: Resource path where mxGraph static files
        are located.
    :param str own_path: Resource path where QmxGraph's own static files
        are located.
    :rtype: str
    :return: HTML contents necessary to load graph drawing widget page.
    """
    from PyQt5.QtCore import QFile
    html_file = QFile(own_path + '/graph.html')

    from PyQt5.QtCore import QIODevice
    if not html_file.open(QIODevice.ReadOnly | QIODevice.Text):
        assert False

    try:
        from jinja2 import Template
        html_data = html_file.readAll().data()
        template = Template(html_data.decode('utf8'))
    finally:
        html_file.close()

    def qrc_prefixed(path):
        return 'qrc{}'.format(path)

    mxgraph_path = qrc_prefixed(mxgraph_path)
    own_path = qrc_prefixed(own_path)
    stencils = [qrc_prefixed(s) for s in stencils]

    return _render(
        template, options, styles, stencils,
        mxgraph_path, own_path, embedded=True)


def render_hosted_html(
        options, styles, stencils, mxgraph_path, own_path, template_path):
    """
    Renders an HTML that is able to load graph drawing widget page in a hosted
    server.

    :param GraphOptions options: Options of graph drawing widget.
    :param GraphStyles styles: Styles available in graph drawing widget.
    :param iterable[str] stencils: Stencils available in graph drawing
        widget.
    :param str mxgraph_path: Path where mxGraph static files are served by
        host server.
    :param str own_path: Path where QmxGraph's own static files are served
        by host server.
    :param str template_path: Path in file system where HTML templates are
        found.
    :rtype: str
    :return: HTML contents necessary to load graph drawing widget page.
    """
    from jinja2 import FileSystemLoader
    from jinja2.environment import Environment

    env = Environment()
    env.loader = FileSystemLoader(template_path)
    template = env.get_template('graph.html')

    return _render(
        template, options, styles, stencils,
        mxgraph_path, own_path, embedded=False)


def _render(
        template, options, styles, stencils, mxgraph_path, own_path, embedded):
    return template.render(
        mxgraph=mxgraph_path,
        own=own_path,
        options=json.dumps(options.as_dict()),
        styles=json.dumps(styles.as_dict()),
        stencils=json.dumps(stencils),
        embedded=embedded,
    )

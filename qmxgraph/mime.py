"""
QmxGraph drag & drop format (MIME type: application/x-qmxgraph-dd)
==================================================================

QmxGraph drag & drop is a JSON object. Format spec is found below:

.. code-block::

    {
        version: <int>,  # version of format used by data, version value is added
                         # since cross application D&D is supported and it is
                         # necessary to know the source version
        vertices:  # optional, vertices are going to be added to graph
            [
                {
                    dx: <int>,  # how much it should displaced in X axis from
                                # where user dropped
                    dy: <int>,  # how much it should displaced in Y axis from
                                # where user dropped
                    width: <int>,  # width of new vertex
                    height: <int>,  # height of new vertex
                    label: <str>,  # label of new vertex
                    style: <str>,  # optional, style of new vertex
                    tags: <dict[str, str]>,  # optional, tags associated
                                             # with vertex
                },
                ...
            ]
        decorations:  # optional, decorations are going to be added to graph
            [
                {
                    width: <int>,  # width of new decoration
                    height: <int>,  # height of new decoration
                    label: <str>,  # label of new decoration
                    style: <str>,  # optional, style of new decoration
                    tags: <dict[str, str]>,  # optional, tags associated
                                             # with decoration
                },
                ...
            ]
    }

"""

import json

import qmxgraph.constants


def create_qt_mime_data(data):
    """
    Creates a Qt's MIME data object for data in valid QmxGraph's drag&drop
    format.

    :param dict data: Contents of MIME data.
    :rtype: QMimeData
    :return: MIME data in QmxGraph format.
    """
    from PyQt5.QtCore import QByteArray, QDataStream, QIODevice, QMimeData
    item_data = QByteArray()
    data_stream = QDataStream(item_data, QIODevice.WriteOnly)

    qgraph_mime = {
        'version': qmxgraph.constants.QGRAPH_DD_MIME_VERSION,
    }
    qgraph_mime.update(data)
    data_stream.writeString(json.dumps(qgraph_mime).encode('utf8'))

    mime_data = QMimeData()
    mime_data.setData(qmxgraph.constants.QGRAPH_DD_MIME_TYPE, item_data)

    return mime_data

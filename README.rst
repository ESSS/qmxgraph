========
QmxGraph
========

.. image:: https://travis-ci.org/ESSS/qmxgraph.svg?branch=master
        :target: https://travis-ci.org/ESSS/qmxgraph

.. image:: https://coveralls.io/repos/github/ESSS/qmxgraph/badge.svg?branch=master
        :target: https://coveralls.io/github/ESSS/qmxgraph?branch=master
        
.. image:: https://api.codacy.com/project/badge/Grade/f99a187898984854a755232cb435cf40
        :alt: Codacy Badge
        :target: https://app.codacy.com/app/ESSS/qmxgraph?utm_source=github.com&utm_medium=referral&utm_content=ESSS/qmxgraph&utm_campaign=badger

This a Qt widget that embeds a rich and powerful graph drawing tool 
using JavaScript's mxGraph library. 

It makes use of Qt web view features to make this possible. Since
current Qt version supported (<= 5.6) is still using WebKit_ as its web
browser engine, all of its limitations apply when developing new embedded web
features.

Due to changes in mxgraph we are currently only supporting an old version of mxgraph (3.7.5).

.. _WebKit: https://webkit.org/

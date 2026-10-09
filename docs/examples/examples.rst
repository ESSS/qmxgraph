========
Examples
========

.. contents::
    :depth: 3
    :local:

The examples here can be found in the examples folder in the project's repository root.

How to run the examples
-----------------------

To run the examples you will need `pixi`_ to setup the environment.

.. code-block:: shell

    git clone https://github.com/ESSS/qmxgraph.git
    cd qmxgraph
    git clone --depth=1 --branch v3.7.5 https://github.com/jgraph/mxgraph.git
    pixi run inv qrc
    # Hello world example.
    pixi run python examples/hello_world/main.py
    # Drag and drop example.
    pixi run python examples/drag_and_drop/main.py

.. _pixi: https://pixi.sh

Hello world
------------

.. literalinclude:: ../../examples/hello_world/main.py
    :language: python
    :linenos:
    :emphasize-lines: 21-24

Basic on styles
---------------

.. literalinclude:: ../../examples/styles/main.py
    :language: python
    :linenos:
    :emphasize-lines: 22-38,56,65,70


Drag&drop and events bridge
---------------------------

.. literalinclude:: ../../examples/drag_and_drop/main.py
    :language: python
    :linenos:
    :emphasize-lines: 39-62,124-130

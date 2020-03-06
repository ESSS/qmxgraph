============
Installation
============

Since pip no longer offers the PyQt version required by qmxgraph you will need `Conda`_ and `conda-devenv`_ to setup the environment.
Until a new version is published the only option is getting the source code.
To install the required dependencies and build the necessary static resources:

.. code-block:: shell

    git clone https://github.com/ESSS/qmxgraph.git
    cd qmxgraph
    git clone --depth=1 --branch v3.7.5 https://github.com/jgraph/mxgraph.git
    export PYTHON_VERSION=3.6  # Optional
    conda devenv
    conda activate qmxgraph
    inv qrc

If you want to run the tests:

.. code-block:: shell
    :emphasize-lines: 5,9

    git clone https://github.com/ESSS/qmxgraph.git
    cd qmxgraph
    git clone --depth=1 --branch v3.7.5 https://github.com/jgraph/mxgraph.git
    export PYTHON_VERSION=3.6  # Optional
    export TEST_QMXGRAPH=1
    conda devenv
    conda activate qmxgraph
    inv qrc
    inv test

.. _Conda: https://docs.conda.io/projects/conda/en/latest/index.html
.. _conda-devenv: https://conda-devenv.readthedocs.io/en/latest/

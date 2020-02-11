#!/bin/bash
echo Using mxgraph $MXGRAPTH_VERSION
git clone --depth=1 --branch $MXGRAPTH_VERSION https://github.com/jgraph/mxgraph.git
export PYTEST_ADDOPTS="--driver PhantomJS"
export MXGRAPHPATH=mxgraph
inv qrc
inv test

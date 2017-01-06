#!/bin/bash
rm -rf mxgraph
git clone --depth=1 https://github.com/jgraph/mxgraph.git
export PYTEST_ADDOPTS="--driver PhantomJS"
export MXGRAPHPATH=mxgraph
inv qrc
inv coverage

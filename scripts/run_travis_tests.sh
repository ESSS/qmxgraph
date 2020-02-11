#!/bin/bash
git clone --depth=1 --branch v4.0.6 https://github.com/jgraph/mxgraph.git
export PYTEST_ADDOPTS="--driver PhantomJS"
export MXGRAPHPATH=mxgraph
inv qrc
inv test

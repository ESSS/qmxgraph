#!/bin/bash
git clone --depth=1 --branch v3.7.5 https://github.com/jgraph/mxgraph.git
export PYTEST_ADDOPTS="--driver PhantomJS"
export MXGRAPHPATH=mxgraph
inv qrc
inv test

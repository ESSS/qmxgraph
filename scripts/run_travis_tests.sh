#!/bin/bash
git clone --depth=1 https://github.com/jgraph/mxgraph.git
export PYTEST_ADDOPTS="--driver PhantomJS"
export MXGRAPHPATH=mxgraph
inv qrc
for i in `seq 1 100`; do echo "*** $i"; inv test; if [ $? != 0 ]; then break; fi; done

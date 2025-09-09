#!/bin/bash
git clone --depth=1 --branch v3.7.5 https://github.com/jgraph/mxgraph.git
export MXGRAPHPATH=mxgraph

export LIBGL_ALWAYS_SOFTWARE=1
export GALLIUM_DRIVER=llvmpipe
export ESSS_SOFTWARE_RENDERING=1
export QT_QUICK_BACKEND=software
export QTWEBENGINE_CHROMIUM_FLAGS="--disable-gpu --no-sandbox"

inv qrc
inv test

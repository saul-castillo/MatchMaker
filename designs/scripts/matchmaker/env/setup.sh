#!/usr/bin/env bash
# Setup MatchMaker environment for the current shell.
# Use:
#   cd /foss/designs
#   source scripts/matchmaker/env/setup.sh

export DESIGNS_ROOT="${DESIGNS_ROOT:-/foss/designs}"
export GLAYOUT_DIR="${GLAYOUT_DIR:-$DESIGNS_ROOT/.external/gLayout}"
export PYTHONPATH="/foss/designs/scripts/matchmaker/src:${PYTHONPATH}"

# gLayout Python source checkout
if [ -d "$GLAYOUT_DIR/src/glayout" ]; then
    export PYTHONPATH="$GLAYOUT_DIR/src:$PYTHONPATH"
elif [ -d "$GLAYOUT_DIR/glayout" ]; then
    export PYTHONPATH="$GLAYOUT_DIR:$PYTHONPATH"
else
    echo "[setup] ERROR: could not find glayout package under $GLAYOUT_DIR"
    echo "[setup] Expected either:"
    echo "  $GLAYOUT_DIR/src/glayout"
    echo "  $GLAYOUT_DIR/glayout"
    return 1 2>/dev/null || exit 1
fi

# EDA tools
export PATH="/foss/tools/klayout:$PATH"
export PATH="/foss/tools/magic/bin:$PATH"
export PATH="/foss/tools/netgen/bin:$PATH"

echo "[setup] DESIGNS_ROOT=$DESIGNS_ROOT"
echo "[setup] GLAYOUT_DIR=$GLAYOUT_DIR"
echo "[setup] klayout=$(command -v klayout || echo MISSING)"
echo "[setup] magic=$(command -v magic || echo MISSING)"
echo "[setup] netgen=$(command -v netgen || echo MISSING)"

python - <<'PY'
import sys
import glayout
import numpy

print("[setup] python:", sys.executable)
print("[setup] glayout:", glayout.__file__)
print("[setup] numpy:", numpy.__version__)
PY
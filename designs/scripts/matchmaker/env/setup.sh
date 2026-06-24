#!/usr/bin/env bash
# Setup MatchMaker/gLayout environment for the current shell.
#
# Use from inside the container:
#   cd /foss/designs
#   source scripts/matchmaker/env/setup.sh
#
# This does not pip-install gLayout. It exposes the local source checkout.

export DESIGNS_ROOT="${DESIGNS_ROOT:-/foss/designs}"
export GLAYOUT_DIR="${GLAYOUT_DIR:-$DESIGNS_ROOT/.external/gLayout}"

if [ ! -d "$GLAYOUT_DIR" ]; then
    echo "[setup] gLayout directory not found:"
    echo "  $GLAYOUT_DIR"
    echo "[setup] Create it with:"
    echo "  mkdir -p $DESIGNS_ROOT/.external"
    echo "  git clone https://github.com/ReaLLMASIC/gLayout.git $GLAYOUT_DIR"
    return 1 2>/dev/null || exit 1
fi

if [ -d "$GLAYOUT_DIR/src/glayout" ]; then
    export PYTHONPATH="$GLAYOUT_DIR/src:$PYTHONPATH"
    export GLAYOUT_PYTHONPATH="$GLAYOUT_DIR/src"
elif [ -d "$GLAYOUT_DIR/glayout" ]; then
    export PYTHONPATH="$GLAYOUT_DIR:$PYTHONPATH"
    export GLAYOUT_PYTHONPATH="$GLAYOUT_DIR"
else
    echo "[setup] Found $GLAYOUT_DIR, but cannot find the glayout Python package."
    echo "[setup] Expected one of:"
    echo "  $GLAYOUT_DIR/src/glayout"
    echo "  $GLAYOUT_DIR/glayout"
    echo "[setup] Current contents:"
    ls -la "$GLAYOUT_DIR" | head
    return 1 2>/dev/null || exit 1
fi

for tool_dir in /foss/tools/klayout /foss/tools/magic/bin /foss/tools/netgen/bin; do
    if [ -d "$tool_dir" ]; then
        export PATH="$tool_dir:$PATH"
    fi
done

echo "[setup] DESIGNS_ROOT=$DESIGNS_ROOT"
echo "[setup] GLAYOUT_DIR=$GLAYOUT_DIR"
echo "[setup] PYTHONPATH added=$GLAYOUT_PYTHONPATH"

python - <<'PY'
import sys
import glayout
print("[setup] python:", sys.executable)
print("[setup] glayout:", glayout.__file__)
PY

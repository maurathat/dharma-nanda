#!/bin/sh
# One-time setup on a new computer. Run from inside the dharma-nanda folder:
#     sh setup.sh
# It needs git and Python 3.11 or newer. Everything it adds stays inside this
# folder (.venv and vendor), so deleting the folder removes it all.
set -e
cd "$(dirname "$0")"
NANDATOWN=6f9a7c064486c4a0ae9242f1ff341b8a4aad0244

PY=""
for c in python3.13 python3.12 python3.11 python3; do
    if command -v "$c" >/dev/null 2>&1 && "$c" -c \
        'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)'; then
        PY="$c"; break
    fi
done
if [ -z "$PY" ]; then
    echo "Python 3.11 or newer is needed. Install it from python.org, then"
    echo "run this again."
    exit 1
fi
echo "Using $PY ($("$PY" --version))"

if [ ! -d vendor/nandatown/.git ]; then
    mkdir -p vendor
    git clone https://github.com/projnanda/nandatown vendor/nandatown
fi
git -C vendor/nandatown checkout -q "$NANDATOWN"

[ -d .venv ] || "$PY" -m venv .venv
.venv/bin/pip install -q --upgrade pip
.venv/bin/pip install -q -e vendor/nandatown -r requirements.txt

echo "Checking that the town runs..."
.venv/bin/python demo.py bytes >/dev/null
echo
echo "Ready. Run the demo steps with:"
echo "    ./run-demo bytes"
echo "    ./run-demo attack"
echo "    ./run-demo seat"
echo "    ./run-demo trace"
echo "    ./run-demo council"
echo "    ./run-demo show"

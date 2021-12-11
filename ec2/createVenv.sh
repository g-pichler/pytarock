#!/bin/bash

rm -rf /opt/venv
python3 -m venv /opt/venv || exit 1

source /opt/venv/bin/activate || exit 1
python3 -m pip install -r /opt/pytarock/requirements.txt || exit 1

exit 0

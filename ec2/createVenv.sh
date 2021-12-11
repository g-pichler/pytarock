#!\bin\bash

rm -rf /opt/venv
python -m venv /opt/venv || exit 1

source /opt/venv/bin/activate || exit 1
python -m pip -r /opt/pytarock/requirements.txt || exit 1

exit 0

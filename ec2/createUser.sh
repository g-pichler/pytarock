#!/bin/bash

id -u pytarock &>/dev/null
if [[ $? -ne 0 ]]; then
  useradd -d /opt/pytarock -M -r pytarock || exit 1
fi

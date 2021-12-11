#!/bin/bash

systemctl daemon-reload || exit 1
systemctl enable pytarock || exit 1
systemctl start pytarock || exit 1

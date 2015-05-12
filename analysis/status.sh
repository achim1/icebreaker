#!/bin/bash

# paths are defined here
source config.sh

python ${ICEBREAKER_DIR}/analysis/status.py
cp ${ICEBREAKER_DIR}/analysis/index.html ${DATA_BASEDIR}/analysis/status
cp ${ICEBREAKER_DIR}/analysis/index.html /var/www/

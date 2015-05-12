#!/usr/bin/env bash

LOAD=`cat /proc/loadavg | cut -d" " -f1`
echo $LOAD

#!/bin/bash

MEM=`cat /proc/meminfo | grep "MemFree" | sed 's/[[:alpha:]]*:[[:space:]]*\([[:digit:]]*\)[[:space:]]*kB/\1/g'`
echo $MEM

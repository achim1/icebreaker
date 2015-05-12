#!/usr/bin/env bash

MONIFILE='monitor.dat'
touch $MONIFILE
while [ true ];
do
    DATE=`date +%Y/%m/%dT%H:%M:%S`
    TEMP=`cat /proc/acpi/thermal_zone/THM/temperature | cut -d' ' -f14`
    LOAD=`cat /proc/loadavg`
    FREQ=`cat /proc/cpuinfo | grep MHz | cut -d' ' -f3`
    FREQ=`echo $FREQ | sed 's/\n/ /'`
    echo $DATE $TEMP $LOAD $FREQ >> $MONIFILE
    sleep 10s
done

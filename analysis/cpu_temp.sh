#!/usr/bin/env bash

TEMP=`cat /proc/acpi/thermal_zone/THM/temperature | cut -d' ' -f14`
echo $TEMP

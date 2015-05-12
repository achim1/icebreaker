#!/bin/bash

UPTIME=`uptime | sed 's/.*up \(.*\),.*users.*/\1/'`
echo $UPTIME

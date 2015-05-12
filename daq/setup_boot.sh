#!/usr/bin/env bash

cp daq /etc/init.d
ln -s /etc/init.d/daq /etc/rc2.d/S99daq
ln -s /etc/init.d/daq /etc/rc3.d/S99daq
ln -s /etc/init.d/daq /etc/rc4.d/S99daq
ln -s /etc/init.d/daq /etc/rc5.d/S99daq
ln -s /etc/init.d/daq /etc/rc1.d/K10daq
ln -s /etc/init.d/daq /etc/rc1.d/K20daq

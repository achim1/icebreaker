#!/usr/bin/env bash

if [ ! -e libbarometers.so ];
then
    make
fi

cp barometer /etc/init.d
ln -s /etc/init.d/barometer /etc/rc2.d/S99barometer
ln -s /etc/init.d/barometer /etc/rc3.d/S99barometer
ln -s /etc/init.d/barometer /etc/rc4.d/S99barometer
ln -s /etc/init.d/barometer /etc/rc5.d/S99barometer
ln -s /etc/init.d/barometer /etc/rc1.d/K10barometer
ln -s /etc/init.d/barometer /etc/rc1.d/K20barometer

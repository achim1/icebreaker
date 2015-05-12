#!/usr/bin/env bash

cp dship /etc/init.d
ln -s /etc/init.d/dship /etc/rc2.d/S99dship
ln -s /etc/init.d/dship /etc/rc3.d/S99dship
ln -s /etc/init.d/dship /etc/rc4.d/S99dship
ln -s /etc/init.d/dship /etc/rc5.d/S99dship
ln -s /etc/init.d/dship /etc/rc1.d/K10dship
ln -s /etc/init.d/dship /etc/rc1.d/K20dship

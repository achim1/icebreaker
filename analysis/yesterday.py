#!/usr/bin/env python

import datetime
import sys

def yesterday():
    one_day = datetime.timedelta(1)
    yesterday = datetime.datetime.utcnow() - one_day
    #yesterday = datetime.datetime.utcnow()
    yesterdays_daq_dir = datetime.datetime.strftime(yesterday,'%Y/%m/%d')
    return yesterdays_daq_dir

def main(argv=None):
    if argv is None:
        argv = sys.argv

    yesterdays_daq_dir = yesterday()
#    yesterdays_daq_dir = datetime.datetime.strftime(datetime.datetime(2011,5,26),'%Y/%m/%d')
    print yesterdays_daq_dir

if __name__ == '__main__':
    main()

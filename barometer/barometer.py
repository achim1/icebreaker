import ctypes
from datetime import datetime
import bz2
import gzip
import os
import logging
import logging.config
import time
import sys
import signal
import daemon

BASEDIR = "/home/cosmic/icebreaker/barometer/"

class Barometer(object):

    def __init__(self):
        self.libbarometer = ctypes.cdll.LoadLibrary(os.path.join(BASEDIR,'libbarometer.so'))
        self.libbarometer.get_pressure.restype = ctypes.c_double
        self.libbarometer.get_temperature.restype = ctypes.c_double
        self.libbarometer.init_devices.restype = ctypes.c_int
        self.datetime_format='%Y/%m/%dT%H:%M:%S'
        self.datetime_path_format='%Y/%m/%d/%Y_%m_%dT%H:%M:%S'
        self.time_format='%H:%M:%S'
        self.interval = 600 #seconds
#        self.interval = 6 #seconds
#        self.baseoutdir = "/media/data/pressure/"
        #self.baseoutdir = "/media/sdcard/pressure"
	self.baseoutdir = "/home/cosmic/rawdata/pressure/"

    def quit(self,signal, frame):
        self.outfile.close()
        self.logger.info('Terminating')
        sys.exit()
    
    def _open_file(self, path):
        dirname = os.path.dirname(path)
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        if path.endswith('.gz'):
            file = gzip.open(path,'w')
        elif path.endswith('.bz2'):
            file = bz2.BZ2File(path,'w')
        else:
            file = open(path,'w')
        return file

    def _get_pathname(self, when):
        filename = datetime.strftime(when, self.datetime_path_format) + '.bz2'
        return os.path.join(self.baseoutdir, filename)

    def init_device(self):
        init_counter = 0
        rv = 1
        while rv != 0 and init_counter < 100:
            rv =  self.libbarometer.init_devices()
            if rv != 0:
                self.logger.error("Could not init pressure sensor")
                self.logger.info('Sleeping 60 seconds')
                time.sleep(60)
        self.logger.info('Initialized pressure sensor')

    def __call__(self):
        # We can only open create the logger here because all open file descriptors
        # are closed when forking the daemon and I don't know how to get the 
        # file descriptor from the logger to preserve it
        logging.config.fileConfig(os.path.join(BASEDIR,'barometer_logging.conf'))
        self.logger = logging.getLogger('barometer')
        self.init_device()
        now = datetime.utcnow()
        last_open_day = now.day
        outfilename = self._get_pathname(now)
        self.outfile =  self._open_file(outfilename)
        self.outfile.write('%s\n'%datetime.strftime(now, self.datetime_format))
        echo = True

        while True:
            pressure = self.libbarometer.get_pressure()/100
            temperature = self.libbarometer.get_temperature()
            if pressure == 0.0:
                self.logger.error('Lost the pressure sensor')
                self.logger.error('Reinitializing device')
                self.init_device()
                time.sleep(10)
                continue
            now = datetime.utcnow()
            if now.day != last_open_day:
                self.outfile.close()
                outfilename = self._get_pathname(now)
                self.outfile = self._open_file(outfilename)
                self.logger.info('Now writing to %s'%outfilename)
                last_open_day = now.day
            now = datetime.strftime(now, self.time_format)
            self.outfile.write('%s %7.2f %7.2f\n'%(now,pressure,temperature))
#            outfile.flush()
            if echo:
                self.logger.debug('%s %7.2f %7.2f'%(now,pressure,temperature))
            time.sleep(self.interval)

if __name__ == '__main__':
    barometer = Barometer()
    import lockfile.pidlockfile
    try:
        #import daemon.pidlockfile
        #daemon.pidfile = daemon.pidlockfile
        daemon.pidfile = lockfile.pidlockfile
    except ImportError:
        import daemon.pidfile
    context = daemon.DaemonContext(
        pidfile=daemon.pidfile.PIDLockFile('/var/run/barometer.pid')
    )
    context.signal_map = {
        signal.SIGHUP: barometer.quit,
        signal.SIGINT: barometer.quit,
        signal.SIGUSR1: barometer.quit,
        signal.SIGTERM: barometer.quit
    }
    with context:
        barometer()

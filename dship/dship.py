import serial
import sys
import time
import os
import re
from optparse import OptionParser
from datetime import datetime, timedelta
from ConfigParser import ConfigParser
import gzip
import bz2
import threading
import Queue
import signal
import logging
import logging.config
import subprocess
import socket

HOME    = "/home/cosmic" # is not $HOME as it might be executed by Ruth
BASEDIR = os.path.join(HOME,"icebreaker/dship/")
OUTDIR  = os.path.join(HOME,"DETECTORDATA/dship/")
ICEDIR  = os.path.join(HOME,"icebreaker")
# hack as we do not want to create a real package here
sys.path.append(ICEDIR)
from filetools.managers import FileWriterFromSocket,FileNamer,datetime_to_pathname,FileWriter


class DShipAgent(object):
    """
    Check for incoming tcp dship stream and write to 
    file
    """
    def __init__(self):
        self.datetime_format='%Y/%m/%dT%H:%M:%S'
        self.datetime_path_format='%Y/%m/%d/%Y_%m_%dT%H:%M:%S'
        self.time_format='%H:%M:%S'
        self.interval = 5 #seconds
        self.baseoutdir = OUTDIR
    
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
    
    def quit(self, signum, frame):
        self.logger.info("Exiting")
        sys.exit(1)

    def __call__(self): # args might be needed by daeomon stuff
        logging.config.fileConfig(os.path.join(BASEDIR, 'dship_logging.conf'))
        self.logger = logging.getLogger("dship")
        port = 1234
        # open the socket
        server_sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        connected = False
        self.logger.info("Will try to accept connections from port %i" %port)
        while not connected:
            try:
                server_sock.bind(("",port))
                connected = True
                self.logger.info("Succesfully bound to port %i" %port)
            except:
                self.logger.error("Cannot bind socket to port %i" %port)
                time.sleep(5)
        server_sock.listen(5)
        client_sock,adress = server_sock.accept()
        adress,port = client_sock.getpeername()
        self.logger.info("Getting peer from %s on port %i" %(adress,port))
        now = datetime.utcnow()
        last_open_day = now.day
        outfilename = self._get_pathname(now)
        self.outfile =  self._open_file(outfilename)
        self.outfile.write("#NMEA DShip data ..") 
        while True:
            now = datetime.utcnow()
            if now.day != last_open_day:
                self.outfile.close()
                outfilename = self._get_pathname(now)
                self.outfile = self._open_file(outfilename)
                self.logger.info('Now writing to %s'%outfilename)
                last_open_day = now.day
            now = datetime.strftime(now, self.time_format)
            item = client_sock.recv(1024)
            self.logger.info("Getting item %s" %item)
            self.outfile.write(item)
            time.sleep(self.interval)

    def __calldepr__(self,args): 
	# somehow the threads cause the daemon to cease running, don't know how to fix this or what the problem is
	
        logging.config.fileConfig(os.path.join(BASEDIR, 'dship_logging.conf'))
        logger = logging.getLogger("dship")
	logger.info("calling")
        self.logger = logger
	port = 1234
        # open the socket
        server_sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
	connected = False
	while not connected:
            try:
                server_sock.bind(("",port))
		connected = True
	    except:
                logger.error("Cannot bind socekt to port %i" %port)
                time.sleep(5)
        server_sock.listen(5)
	newsock,adress = server_sock.accept()
        client_sock = newsock
        adress,port = newsock.getpeername()
        logger.info("Getting peer from %s on port %i" %(adress,port))
	now = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')
        default_filename = 'dship_' + now + '.txt.gz'
        newfilequeue = Queue.Queue()
        dataqueue = Queue.Queue() # I suspect sockets can not be cross-thread unfortunately

        namer = FileNamer(OUTDIR, newfilequeue, 3600,prefix="dship_")
        outfile = os.path.join(OUTDIR, datetime_to_pathname(datetime.utcnow()))
        #writer = FileWriterFromSocket(outfile, client_sock, newfilequeue,loggername="dship")
        writer = FileWriter(outfile, dataqueue, newfilequeue,loggername="dship")
        self.threads = [(obj,threading.Thread(target=obj)) for obj in (namer, writer)]
	logger.info("starting threads")
        for thread in self.threads:
            thread[1].setDaemon(True)
            thread[1].start()

        while True:
	    logger.info("sleeping")
	    time.sleep(10)

if __name__ == '__main__':
    dship = DShipAgent()
    if '-d' in sys.argv:
        args = sys.argv[:]
        args.remove('-d')
        import daemon
	import lockfile.pidlockfile
        try:
            #import daemon.pidlockfile
            #daemon.pidfile = daemon.pidlockfile
            daemon.pidfile = lockfile.pidlockfile
        except:
            import daemon.pidfile
        context = daemon.DaemonContext(
            pidfile=daemon.pidfile.PIDLockFile('/var/run/dship.pid')
        )
        context.signal_map = {
            signal.SIGHUP: dship.quit,
            signal.SIGINT: dship.quit,
            signal.SIGUSR1: dship.quit,
            signal.SIGTERM: dship.quit
        }
        with context:
            dship()
    else:
        signal.signal(signal.SIGHUP,  dship.quit)
        signal.signal(signal.SIGINT,  dship.quit)
        signal.signal(signal.SIGUSR1, dship.quit)
        signal.signal(signal.SIGTERM, dship.quit)
        dship()

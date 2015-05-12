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


BASEDIR = "/home/cosmic/icebreaker/daq"

class FileWriter(object):

    def __init__(self, path, inqueue, filenamequeue):
        self.logger = logging.getLogger("daq")
        if os.path.exists(path):
            raise ValueError('File %s already exists'%path)
        self.file = self._open(path)
        self.inqueue = inqueue
        self.filenamequeue = filenamequeue
        self.halt = False

    def _open(self, path):
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

    def _new_file(self):
        self.logger.info("FileWriter: Getting new filename")
        path = self.filenamequeue.get()
        self.logger.info("FileWriter: Now writing to %s"%path)
        self.file.close()
        self.file = self._open(path)

    def _write_time(self):
        now = datetime.utcnow()
        to_write = datetime.strftime(now,'%Y%m%dT%H:%M:%S')
        to_write += '.%i\n'%now.microsecond
        self.file.write(to_write)

    def __call__(self):
        new_file = False
        while not self.halt:
            if not self.filenamequeue.empty():
                self._new_file()
                new_file = True
            try:
                item = self.inqueue.get(timeout=0.01)
                self.file.write(item)
#                    self.file.flush()
            except Queue.Empty:
                time.sleep(0.05)
            if new_file:
                self._write_time()
                new_file = False
        self.logger.info("Stopping FileWriter")
        self.file.close()

class CommandIssuer(object):
    'Put commands into a queue at regular intervals'

    def __init__(self, commandqueue):
        self.logger = logging.getLogger("daq")
        self.commandqueue = commandqueue
        self.commandlist = []
        self.halt = False

    def add(self, command, seconds):
        '''
        Arguments:
            command - DAQ command as a string
            seconds - Interval in seconds
        '''
        delta = timedelta(0, seconds)
        self.commandlist.append([None, (command, delta)])

    def issue_command(self, command):
        self.logger.debug('Issueing %s'%command.rstrip('\n\r'))
        self.commandqueue.put(command)

    def __call__(self):
        for command in self.commandlist:
            self.issue_command(command[1][0])
            command[0] = datetime.utcnow() + command[1][1]
            # Sleep a little between the commands so we don't have to issue them
            # all at the same time in the future
            time.sleep(0.1)
        self.commandlist.sort()
        next_call_time = self.commandlist[0][0]
        now = datetime.utcnow()
        sleeptime = next_call_time - now
        self.logger.debug('Sleeping %f'%sleeptime.seconds)
        if not self.halt:
            time.sleep(sleeptime.seconds + sleeptime.microseconds/1e6)
        while not self.halt:
            if len(self.commandlist) > 0:
                now = datetime.utcnow()
                next_call_command = self.commandlist[0][1][0]
                next_call_interval = self.commandlist[0][1][1]
                next_call_time = self.commandlist[0][0]
                sleeptime = next_call_time - now
                sleeptime_seconds = sleeptime.seconds + sleeptime.microseconds/1e6
                if sleeptime_seconds < 0. or sleeptime.days < 0:
                    sleeptime_seconds = 0.1
                self.logger.debug('Sleeping %f'%sleeptime_seconds)
                time.sleep(sleeptime_seconds)
                self.issue_command(next_call_command)
                self.commandlist[0][0] += next_call_interval
                self.commandlist.sort()
        self.logger.info("Stopping CommandIssuer")


class DaqConnector(object):

    def __init__(self, get_port, setup_daq, commandqueue, dataqueue):
        self.logger = logging.getLogger("daq")
        self.get_port = get_port
        self.setup_daq = setup_daq
        self.port = self.get_port(self.logger)
        self.setup_daq.setup(commandqueue)
        self.commandqueue = commandqueue
        self.dataqueue = dataqueue
        self.halt = False
        self.good_pattern = re.compile("^[a-zA-Z0-9+-.,:()=$/#?!%_@*|~' ]*[\n\r]*$")

    def __call__(self):
        while not self.halt:
            while not self.commandqueue.empty():
                message = self.commandqueue.get()
                self.logger.debug('Sending %s'%message)
                self.port.write(message)
            try:
                while self.port.inWaiting():
                    line = self.port.readline()
                    # Check if the line only contains alphanumeric characters or spaces
                    if self.good_pattern.match(line) is None:
                        # Do something more sensible here, like stopping the DAQ
                        # then wait until service is restarted?
                        self.logger.error("Got garbage from the DAQ: %s"%line.rstrip('\r\n'))
                        self.port.close()
                        self.port = self.get_port(self.logger)
                        self.setup_daq.setup(self.commandqueue)
                    self.dataqueue.put(line)
            except IOError:
                self.logger.error("IOError")
                self.port.close()
                self.port = self.get_port(self.logger)
                self.setup_daq.setup(self.commandqueue)
            except OSError:
                self.logger.error("IOError")
                self.port.close()
                self.port = self.get_port(self.logger)
                self.setup_daq.setup(self.commandqueue)
            time.sleep(0.01)
        self.logger.info("Stopping DaqConnector")

class FakeDaqConnector(object):

    def __init__(self, commandqueue, dataqueue):
        self.logger = logging.getLogger("daq")
        self.file = open('/home/cosmic/icebreaker/daq/fakedata.txt')
        self.dataqueue = dataqueue
        rate = 100 # per second
        self.sleeptime = 1./rate
        self.halt = False

    def __call__(self):
        while not self.halt:
            line = self.file.readline()
            if len(line) == 0:
                self.file.seek(0)
                continue
            self.dataqueue.put(line)
            time.sleep(self.sleeptime)
        self.file.close()
        self.logger.info("Exiting FakeDaqConnector")

def datetime_to_pathname(when):
    format = '%Y/%m/%d/%Y_%m_%dT%H:%M:%S.bz2'
    return datetime.strftime(when, format)

class FileNamer(object):

    def __init__(self, basedir, filenamequeue, seconds):
        self.logger = logging.getLogger("daq")
        self.filenamequeue = filenamequeue
        self.basedir = basedir
        self.halt = False
        self.seconds = seconds

    def __call__(self):
        delta = timedelta(seconds=self.seconds)
        while not self.halt:
            now = datetime.utcnow()
            this_hour = datetime(now.year,now.month,now.day,now.hour,0,0,0)
#            this_hour = datetime.utcnow()
            next_file_date = this_hour + delta
            self.logger.debug("FileNamer: Next file will be started at",next_file_date)
            sleeptime = next_file_date - now
            self.logger.debug("FileNamer: Sleeping %i seconds"%sleeptime.seconds)
            time.sleep(sleeptime.seconds + 1.0)
            new_path = os.path.join(self.basedir, datetime_to_pathname(datetime.utcnow()))
            self.filenamequeue.put(new_path)
        self.logger.info("Stopping FileNamer")

def get_port(logger):
    connected = False
    while not connected:
        dev = subprocess.Popen([os.path.join(BASEDIR, 'which_tty_daq')], stdout=subprocess.PIPE).communicate()[0]
        dev = "/dev/" + dev
        dev = dev.rstrip('\n')
        logger.info("Daq connected to %s",dev)
        try:
            port = serial.Serial(port=dev, baudrate=115200,
                                 bytesize=8,parity='N',stopbits=1,
                                 timeout=1,xonxoff=True)
            connected = True
        except serial.SerialException, e:
            logger.error(e)
            logger.error("Waiting 10 seconds")
            time.sleep(10)
    logger.info("Successfully connected to serial port")
    return port

class MuonTelescope(object):
    def __init__(self, thresh_ch0, thresh_ch1, thresh_ch2, thresh_ch3):
        self.thresh_ch0 = thresh_ch0
        self.thresh_ch1 = thresh_ch1
        self.thresh_ch2 = thresh_ch2
        self.thresh_ch3 = thresh_ch3

    def setup(self, commandqueue):
        # setup simple muon telesope
        commandqueue.put('RB\r')
        commandqueue.put('TI\r')
        commandqueue.put('CD\r')
#        commandqueue.put('WC 00 0F\r') # Singles with channels 0,1,2,4
        #commandqueue.put('WC 00 1F\r') # Double coincidences with channels 0,1,2,4
        commandqueue.put('WC 00 3F\r') # fourfold coincidences with channels 0,1,2,4
        commandqueue.put('WC 01 00\r')
        commandqueue.put('WC 02 0A\r') # gate width 10 clockticks (10 * 10 ns)
        commandqueue.put('WC 03 00\r')
        commandqueue.put('WT 01 00\r') # TMC delay= 4 clockticks (4 * 10 ns)
        commandqueue.put('WT 02 04\r')
        # Set thresholds
        for i,thresh in enumerate((self.thresh_ch0, self.thresh_ch1, self.thresh_ch2, self.thresh_ch3)):
            commandqueue.put('TL ' + str(i) + ' ' + str(thresh) + '\r')
        commandqueue.put('TL\r')
        commandqueue.put('DC\r')
        commandqueue.put('DG\r')
        commandqueue.put('DS\r')
        commandqueue.put('DT\r')
        commandqueue.put('BA\r')
        commandqueue.put('TH\r')
        commandqueue.put('CE\r')

class Daq(object):

    def __init__(self):
        pass

    def quit(self, signum, frame):
        self.logger.info("Exiting")
        for i,_ in enumerate(self.threads):
            self.threads[i][0].halt = True
        time.sleep(0.5)
        sys.exit(1)

    def __call__(self, args):

        logging.config.fileConfig(os.path.join(BASEDIR, 'daq_logging.conf'))
        self.logger = logging.getLogger("daq")
        now = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')
        default_filename = 'daq_' + now + '.txt.gz'
        parser = OptionParser()
        parser.add_option('-c','--configfile',dest='cfgfile',
                           default='/home/cosmic/icebreaker/daq/daq.cfg',help='Path to the config file')
        parser.add_option('-f','--fake',dest='fake',action='store_true',
                           default=False,help='Read fake DAQ data from file')
        (options, args) = parser.parse_args(args)
        cfgfilename = options.cfgfile
        self.logger.info("Reading config from %s"%cfgfilename)
        fake = options.fake

        config = ConfigParser()
        config.readfp(open(cfgfilename))
        outdir = config.get('output','dir')
        thresh_ch0 = config.getint('daq','thresh_ch0')
        thresh_ch1 = config.getint('daq','thresh_ch1')
        thresh_ch2 = config.getint('daq','thresh_ch2')
        thresh_ch3 = config.getint('daq','thresh_ch3')

        dataqueue = Queue.Queue()
        commandqueue = Queue.Queue()
        newfilequeue = Queue.Queue()

        namer = FileNamer(outdir, newfilequeue, 3600)
        outfile = os.path.join(outdir, datetime_to_pathname(datetime.utcnow()))
        writer = FileWriter(outfile, dataqueue, newfilequeue)
        commander = CommandIssuer(commandqueue)
        muon_telescope = MuonTelescope(thresh_ch0, thresh_ch1, thresh_ch2, thresh_ch3)
        if fake:
            daq = FakeDaqConnector(commandqueue, dataqueue)
        else:
            daq = DaqConnector(get_port, muon_telescope, commandqueue, dataqueue)

        # These commands are executed regularly
        commander.add('DG\r',1800)
        commander.add('TH\r',1800)
        commander.add('BA\r',1800)
        for command in ['H1','H2','DC','DS','DT','TI','V1','V2','V3','ST 3 15','SA 1','CE']:
            commander.add(command+'\r',43000) #Roughly every 12 hours
#        for command in ['H1','H2','DC','DS','DT','TI','V1','V2','V3','ST 3 1','SA 1','CE']:
#            commander.add(command+'\r',60) #Once per minute

        self.threads = [(obj,threading.Thread(target=obj)) for
                    obj in (namer, commander, daq, writer)]
        for thread in self.threads:
            thread[1].setDaemon(True)
            thread[1].start()

        while True:
            time.sleep(10)

if __name__ == '__main__':
    daq = Daq()
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
            pidfile=daemon.pidfile.PIDLockFile('/var/run/daq.pid')
        )
        context.signal_map = {
            signal.SIGHUP: daq.quit,
            signal.SIGINT: daq.quit,
            signal.SIGUSR1: daq.quit,
            signal.SIGTERM: daq.quit
        }
	with context:
            daq(args)
    else:
        signal.signal(signal.SIGHUP, daq.quit)
        signal.signal(signal.SIGINT, daq.quit)
        signal.signal(signal.SIGUSR1, daq.quit)
        signal.signal(signal.SIGTERM, daq.quit)
        daq(sys.argv)

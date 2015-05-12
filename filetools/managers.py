"""
Utils to manage automatic file generation every XX seconds
"""

import logging
import bz2
import time
import os.path
import os
from datetime import datetime,timedelta

def datetime_to_pathname(when):
    format = '%Y/%m/%d/%Y_%m_%dT%H:%M:%S.bz2'
    return datetime.strftime(when, format)



class FileNamer(object):
    """
    Name files accordingly to the date
    """
    def __init__(self, basedir, filenamequeue, seconds,loggername="daq",prefix=""):
        self.logger = logging.getLogger(loggername)
        self.filenamequeue = filenamequeue
        self.basedir = basedir
        self.halt = False
        self.seconds = seconds
        self.prefix = prefix

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


class FileWriter(object):

    def __init__(self, path, inqueue, filenamequeue,loggername="daq"):
        self.logger = logging.getLogger(loggername)
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

class FileWriterFromSocket(FileWriter):
    """
    A FileWriter which works for sockets instead of 
    queues
    """

    def __init__(self, path, socket, filenamequeue,loggername="daq"):

        FileWriter.__init__(self,path,socket,filenamequeue,loggername=loggername)
        self.socket = socket
        del self.inqueue

    def __call__(self):
        new_file = False
        while not self.halt:
            if not self.filenamequeue.empty():
                self._new_file()
                new_file = True
                #filestarttime = time.time()
            try:
                item = self.socket.recv(1024)
                self.logger.info("Writing %s to file" %item)
		self.file.write(item)
#                    self.file.flush()
            except Exception as e:
                time.sleep(0.05)
            if new_file:
                self._write_time()
                new_file = False
        self.logger.info("Stopping FileWriter")
        self.file.close()


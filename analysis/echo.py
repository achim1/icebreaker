# Echo server program
import socket
import signal
import sys

def quit(signum, frame):
    global conn
    conn.close()
    sys.exit(1)

def read(conn):
    while 1:
        data = conn.recv(1024)
        if not data: break
        #print data
        out.write('%s'%data)

HOST = ''                 # Symbolic name meaning all available interfaces
PORT = 1234
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((HOST, PORT))
s.listen(1)
conn, addr = s.accept()
print 'Connected by', addr
signal.signal(signal.SIGHUP, quit)
signal.signal(signal.SIGINT, quit)
signal.signal(signal.SIGUSR1, quit)
signal.signal(signal.SIGTERM, quit)
out = open('/media/usbstick/data/pressure/time-gps-weather.dat','w')
read(conn)

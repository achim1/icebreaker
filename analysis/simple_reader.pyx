import sys
import gzip
import bz2
from operator import itemgetter
from tools import time_to_seconds, Pulse, MuonFinder
from tools cimport Pulse, MuonFinder

cdef int BIT0_4 = 31
cdef int BIT5 = 1 << 5
cdef int BIT7 = 1 << 7

# For DAQ status
cdef int BIT0 = 1 # 1 PPS interrupt pending
cdef int BIT1 = 1 << 1 # Trigger interrupt pending
cdef int BIT2 = 1 << 2 # GPS data possible corrupted
cdef int BIT3 = 1 << 3 # Current or last 1PPS rate not within range

#freq = 41666667.0
cdef double freq = 25.0e6
cdef double MINI_TICK = 1.0/(freq * 32)

cdef double COINC_WIND = 200e-9 #Time window for which we count two pulses as coincident
cdef double MUON_WIND = 200e-9 # Time window in which we require hits in the two szintillators to count as a muon


def muon_printer(channels):
    muon_time = min([t for t in channels.itervalues() if t != 0.])
    print "MUON %.3f"%muon_time,[k for k,v in channels.iteritems() if v != 0.0]

def analyze_files(filelist, callback=muon_printer):

    cdef bint verbose = False
    cdef Pulse pulse0 = Pulse(0)
    cdef Pulse pulse1 = Pulse(1)
    cdef Pulse pulse2 = Pulse(2)
    cdef Pulse pulse3 = Pulse(3)

    cdef int pulse_counter = 0
    cdef MuonFinder muon_finder = MuonFinder(callback, MUON_WIND, muon=((0,2),(0,3),(1,2),(1,3)))
    cdef long long last_onepps_count = 0
    cdef bint gps_valid = True
    cdef long long trigger_count
    cdef long long onepps_count
    cdef int nfields
    cdef double seconds
    cdef double line_time
    cdef int err,re0,fe0,re1,fe1,re2,fe2,re3,fe3

    for filename in filelist:
        if filename.endswith('.bz2'):
            f = bz2.BZ2File(filename)
        elif filename.endswith('.gz'):
            f = gzip.open(filename)
        else:
            f = open(filename)
        all_pulses = []
        #try:
        #    for line in f.readlines():
        #        pass # check file integrity
        #except:
        #    continue # if we log, nobody will read anyway, so skip it     
        for line in f:
            if verbose: print line
            fields = line.rstrip("\n").split(" ")
            nfields = len(fields)
            # Ignore malformed lines
            if nfields != 16:
                continue
            #Ignore everything that is not trigger data
            if len(fields[0]) != 8:
                continue
            # Check if GPS data is valid
#            if fields[12] != "A":
#                if gps_valid: print "Error: GPS data not valid"
#                gps_valid = False
#                continue
            gps_valid = True
            #Another check, sometimes lines are mixed,
            #try if we can convert the last field to an int
            try:
                int(fields[nfields-1])
            except ValueError:
                continue
#        Check if error bits are set
            if fields[14] != "0":
                err = int(fields[14],16)
                if (err & BIT0) != 0:
                    print 'Error: 1 PPS interrupt pending',
                if (err & BIT1) != 0:
#                    print 'Error: Trigger interrupt pending',
                    pass
                if (err & BIT2) != 0:
                    print 'Error: GPS data corrupt',
                if (err & BIT3) != 0:
#                    print 'Error: 1PPS rate not within range',
                    pass
#                print line.rstrip('\n')
#                continue
            trigger_count = int(fields[0],16)
            onepps_count = int(fields[9],16)
            if onepps_count != last_onepps_count:
                if verbose:
                    print "PPS:",onepps_count - last_onepps_count
                last_onepps_count = onepps_count

            trigger = (int(fields[1],16) & BIT7) != 0

            time = fields[10]
            correction = fields[15]
            seconds = time_to_seconds(time,correction)
            line_time = seconds + (trigger_count - onepps_count)/freq
            if trigger:
                if verbose: print "Trigger: %10.12f"%(line_time,)
                pulse0.invalidate()
                pulse1.invalidate()
                pulse2.invalidate()
                pulse3.invalidate()

            re0 = int(fields[1],16)
            if re0 & BIT5 != 0:
                time = line_time + (re0 & BIT0_4) * MINI_TICK
                pulse0.rise(time)
                if verbose: print "0> %10.12f"%(time,)
            fe0 = int(fields[2],16)
            if fe0 & BIT5 != 0:
                time = line_time + (fe0 & BIT0_4) * MINI_TICK
                pulse0.fall(time)
                if verbose: print "0< %10.12f"%(time,)
            re1 = int(fields[3],16)
            if re1 & BIT5 != 0:
                time = line_time + (re1 & BIT0_4) * MINI_TICK
                pulse1.rise(time)
                if verbose: print "1> %10.12f"%(time,)
            fe1 = int(fields[4],16)
            if fe1 & BIT5 != 0:
                time = line_time + (fe1 & BIT0_4) * MINI_TICK
                pulse1.fall(time)
                if verbose: print "1< %10.12f"%(time,)
            re2 = int(fields[5],16)
            if re2 & BIT5 != 0:
                time = line_time + (re2 & BIT0_4) * MINI_TICK
                pulse2.rise(time)
                if verbose: print "2> %10.12f"%(time,)
            fe2 = int(fields[6],16)
            if fe2 & BIT5 != 0:
                time = line_time + (fe2 & BIT0_4) * MINI_TICK
                pulse2.fall(time)
                if verbose: print "2< %10.12f"%(time,)
            re3 = int(fields[7],16)
            if re3 & BIT5 != 0:
                time = line_time + (re3 & BIT0_4) * MINI_TICK
                pulse3.rise(time)
                if verbose: print "3> %10.12f"%(time,)
            fe3 = int(fields[8],16)
            if fe3 & BIT5 != 0:
                time = line_time + (fe3 & BIT0_4) * MINI_TICK
                pulse3.fall(time)
                if verbose: print "3< %10.12f"%(time,)

            pulses = []

            if pulse0.valid:
                if verbose: print "0:",pulse0.width()
                pulses.append(pulse0)
                pulse0 = Pulse(0)
            if pulse1.valid:
                if verbose: print "1:",pulse1.width()
                pulses.append(pulse1)
                pulse1 = Pulse(1)
            if pulse2.valid:
                if verbose: print "2:",pulse2.width()
                pulses.append(pulse2)
                pulse2 = Pulse(2)
            if pulse3.valid:
                if verbose: print "3:",pulse3.width()
                pulses.append(pulse3)
                pulse3 = Pulse(3)

            pulses.sort()
            for pulse in pulses:
                muon_finder.analyze_pulse(pulse)

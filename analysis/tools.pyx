from libc.string cimport strtok
from libc.stdlib cimport atoi
from libc.math cimport floor

# That was the python prototype for the Cython implementation
#def time_to_seconds(time, correction):
    #    '''
    #Convert hhmmss,xxx string int seconds since day start
    #'''
#    print time,correction
#    tfields = time.split(".")
#    t = tfields[0]
#    secs_since_day_start = int(t[0:2])*3600+int(t[2:4])*60+int(t[4:6])
#    evt_time = secs_since_day_start + int(tfields[1])/1000.0+int(correction)/1000.0
#    return round(evt_time)

cpdef int time_to_seconds(char *time, char *correction):
    '''
    Convert hhmmss,xxx string int seconds since day start
    '''
    cdef char * token
    token = strtok(time,".")
    cdef char timeitem[2]
    timeitem[0] = token[0]
    timeitem[1] = token[1]
    cdef int hour = atoi(timeitem)
    timeitem[0] = token[2]
    timeitem[1] = token[3]
    cdef int minute = atoi(timeitem)
    timeitem[0] = token[4]
    timeitem[1] = token[5]
    cdef int second = atoi(timeitem)
    cdef int secs_since_day_start = hour*3600 + minute*60 + second
    cdef int corr = atoi(correction)
    token = strtok(NULL,".")
    cdef double evt_time = secs_since_day_start + atoi(token)/1000.0 + corr/1000.0
    return <int>floor(evt_time + 0.5)


cdef class Pulse:

    def __init__(self, int channel):
        self.channel = channel
        self.valid = False
        self.wait_falling = False
        self.valid = 0
        self.wait_falling = 0

    def __richcmp__(self, Pulse other, int op):
        if op == 0:
            return self.rise_time < other.rise_time
        elif op == 1:
            return self.rise_time <= other.rise_time
        elif op == 2:
            return self.rise_time == other.rise_time
        elif op == 3:
            return self.rise_time != other.rise_time
        elif op == 4:
            return self.rise_time > other.rise_time
        elif op == 5:
            return self.rise_time >= other.rise_time

    cpdef rise(self, double time):
        self.wait_falling = True
        self.rise_time = time

    cpdef fall(self, double time):
        if self.wait_falling:
            self.fall_time = time
            self.valid = True
            self.wait_falling = False
#            print "TOT",self.channel,(time - self.rise_time) * 1e9

    cpdef invalidate(self):
        self.valid = False

    cpdef double width(self):
        if self.valid:
            return 1e9 * (self.fall_time - self.rise_time)

cdef class MuonFinder:

    def __init__(self, muon_callback, double time_window, muon=((0,2),(0,3),(1,2),(1,3))):
        self.muon_callback = muon_callback
        self.muon = muon
        self.channels = {0:0.,1:0.,2:0.,3:0.}
        self.lastpulse_time = 0.
        self.time_window = time_window

    cpdef reset(self):
        for key in self.channels.iterkeys():
            self.channels[key] = 0.

    cpdef bint coincidence_found(self):
        for comb in self.muon:
            coinc = True
            for ch in comb:
                if self.channels[ch] == 0.:
                    coinc = False
                    break
            if coinc:
                return True
        return False

    cpdef analyze_pulse(self, Pulse pulse):
        if 0 < pulse.rise_time - self.lastpulse_time < self.time_window or self.lastpulse_time == 0.:
            self.channels[pulse.channel] = pulse.rise_time
            self.lastpulse_time = pulse.rise_time
        else:
            if self.coincidence_found():
                self.muon_callback(self.channels)
            self.reset()
            self.channels[pulse.channel] = pulse.rise_time
            self.lastpulse_time = pulse.rise_time



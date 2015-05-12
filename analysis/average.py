#!/usr/bin/env python

class AverageRate(object):

    def __init__(self, interval):
        self.interval = interval
        self.started = False
        self.bin_start = 0.
        self.n = 0

    def fits(self, time):
        if not self.started:
            return True
        return time - self.bin_start <= self.interval

    def put(self, time,weight=1):


        if not self.started:
            self.bin_start = time
            self.started = True
        if self.fits(time):
            self.n += (1*weight)
            self.last_time = time
        else:
            raise ValueError()
    
    def avg(self):
        return self.n/float(self.interval)

    def reset(self):
        self.n = 0
        self.bin_start = self.last_time

if __name__ == "__main__":
    import sys
    INTERVAL = 3600.
    inputfile = sys.argv[1]
    coincidence_level = int(sys.argv[2])
    f = open(inputfile)
    avg = AverageRate(INTERVAL)
    for line in f.xreadlines():
        line = line.split()
	pulses = eval("".join(line[1:]))
	line = line[0]
	#print pulses,len(pulses)
        try:
            val = float(line)
        except:
            continue
        try:
	    if len(pulses) >= coincidence_level:
            	avg.put(val)
        except ValueError:
            print avg.bin_start, avg.avg()
            avg.reset()
    

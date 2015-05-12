import sys
import os
import gzip
import bz2
from datetime import datetime,time
from datetimeconv import datetime2mjd
import ROOT
import array
from operator import itemgetter

BIT0_4 = 31
BIT5 = 1 << 5
BIT7 = 1 << 7

# For DAQ status
BIT0 = 1 # 1 PPS interrupt pending
BIT1 = 1 << 1 # Trigger interrupt pending
BIT2 = 1 << 2 # GPS data possible corrupted
BIT3 = 1 << 3 # Current or last 1PPS rate not within range

#freq = 41666667.0
freq = 25.0e6
MINI_TICK = 1.0/(freq * 32)

MIDNIGHT = time(0,0,0)
SEC_PER_DAY = 86400.

#TODO: Add number of visible satellites and GPS status to the root file

def filename_to_datetime(name):
    format = '%Y_%m_%dT%H:%M:%S.bz2'
    return datetime.strptime(name, format)

def time_to_seconds(time, correction):
    '''
    Convert hhmmss,xxx string int seconds since day start
    '''
#    print time,correction
    tfields = time.split(".")
    t = tfields[0]
    secs_since_day_start = int(t[0:2])*3600+int(t[2:4])*60+int(t[4:6])
    evt_time = secs_since_day_start + int(tfields[1])/1000.0+int(correction)/1000.0
    return round(evt_time)

class Pulse(object):
    def __init__(self, channel):
        self.channel = channel
        self.valid = False
        self.wait_falling = False

    def rise(self, time):
        self.wait_falling = True
        self.rise_time = time

    def fall(self, time):
        if self.wait_falling:
            dt = 1e9 * (time - self.rise_time)
            if 0 < dt < 500:
                self.fall_time = time
                self.valid = True
                self.wait_falling = False
#            print "TOT",self.channel,(time - self.rise_time) * 1e9

    def invalidate(self):
        self.valid = False

    def width(self):
        if self.valid:
            return 1e9 * (self.fall_time - self.rise_time)
        else:
            raise ValueError()

def analyze_files(filelist, rootfilename=None):

    if rootfilename is None:
        rootfilename = os.path.basename(filelist[0])+".root"
    outfile = ROOT.TFile(rootfilename,"RECREATE")
    tree = ROOT.TTree("aTree","aTree")
    channel = array.array('I',[0])
    event_time = array.array('d',[0.])
    event_mjd = array.array('d',[0.])
    pulse_width = array.array('d',[0.])
    tree.Branch("ChannelID",channel,"ChannelID/I")
    tree.Branch("EventTimeMJD",event_mjd,"EventTimeMJD/D")
    tree.Branch("EventSecOfDay",event_time,"EventSecOfDay/D")
    tree.Branch("PulseWidth",pulse_width,"PulseWidth/D")

    verbose = False
    pulse0 = Pulse(0)
    pulse1 = Pulse(1)
    pulse2 = Pulse(2)
    pulse3 = Pulse(3)

    pulse_counter = 0
    last_onepps_count = 0
    gps_valid = True
    pulses = []

    for filename in filelist:
        if filename.endswith('.bz2'):
            f = bz2.BZ2File(filename)
        elif filename.endswith('.gz'):
            f = gzip.open(filename)
        else:
            f = open(filename)
        all_pulses = []
        try:
            f.readlines()
        except:
            # Don't try to read broken files
            continue
        f.seek(0)
        for line in f:
            if verbose: print line
            fields = line.rstrip("\n").split(" ")
            # Ignore malformed lines
            if len(fields) != 16:
                continue
            #Ignore everything that is not trigger data
            if len(fields[0]) != 8:
                continue
            #Ignore times when we see no satellites
            if int(fields[13]) == 0:
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
                int(fields[len(fields)-1])
            except ValueError:
                continue
            try:
                int(fields[0],16)
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
            date = fields[11]
            date = '.'.join((date[0:2],date[2:4],'20'+date[4:6]))
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


            if pulse0.valid:
                width = pulse0.width()
                if verbose: print "0:",width
                mjd = datetime2mjd(date,MIDNIGHT) + pulse0.rise_time/SEC_PER_DAY
                sortkey = (int(mjd),pulse0.rise_time)
                pulses.append((0,pulse0.rise_time,mjd,width,sortkey))
                pulse0.invalidate()
            if pulse1.valid:
                width = pulse1.width()
                if verbose: print "1:",width
                mjd = datetime2mjd(date,MIDNIGHT) + pulse1.rise_time/SEC_PER_DAY
                sortkey = (int(mjd),pulse1.rise_time)
                pulses.append((1,pulse1.rise_time,mjd,width,sortkey))
                pulse1.invalidate()
            if pulse2.valid:
                width = pulse2.width()
                if verbose: print "2:",width
                mjd = datetime2mjd(date,MIDNIGHT) + pulse2.rise_time/SEC_PER_DAY
                sortkey = (int(mjd),pulse2.rise_time)
                pulses.append((2,pulse2.rise_time,mjd,width,sortkey))
                pulse2.invalidate()
            if pulse3.valid:
                width = pulse3.width()
                if verbose: print "3:",width
                mjd = datetime2mjd(date,MIDNIGHT) + pulse3.rise_time/SEC_PER_DAY
                sortkey = (int(mjd),pulse3.rise_time)
                pulses.append((3,pulse3.rise_time,mjd,width,sortkey))
                pulse3.invalidate()

    pulses.sort(key=itemgetter(4))
    for pulse in pulses:
        channel[0] = pulse[0]
        event_time[0] = pulse[1]
        event_mjd[0] = pulse[2]
        pulse_width[0] = pulse[3]
        tree.Fill()
    tree.Write()
    outfile.Close()

def get_files(dir):
    daqfiles = []
    for _,_,files in os.walk(dir):
        for file in files:
            if file.endswith(".bz2"):
                daqfiles.append(os.path.join(dir,file))
    return daqfiles

def path_to_rootfilename(path):
    comp = path.split(os.path.sep)[-3:]
    new = os.path.join(*comp)
    format = '%Y/%m/%d'
    try:
        when = datetime.strptime(new,format)
    except ValueError:
        print "Could not parse directory name"
        sys.exit(1)
    filenameformat = '%Y_%m_%d.root'
    return datetime.strftime(when,filenameformat)

def main(argv=None):
    if argv is None:
        argv = sys.argv
    if os.path.isdir(argv[1]):
        rootfilename = path_to_rootfilename(argv[1])
        daqfiles = sorted(get_files(argv[1]))
        analyze_files(daqfiles, rootfilename)
    else:
        analyze_files(argv[1:])

if __name__ == '__main__':
    main()

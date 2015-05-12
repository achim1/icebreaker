import matplotlib
import pylab
import matplotlib.pyplot as plt
from datetime import datetime

def prescale(l, factor = 10):
    return [el for i,el in enumerate(l) if i%factor==0]

format='%Y/%m/%dT%H:%M:%S'
filename = 'monitor.dat'
dates = [datetime.strptime(f.split()[0],format) for f in open(filename).readlines()]
temps = [float(f.split()[1]) for f in open(filename).readlines()]
load_15min = [float(f.split()[2]) for f in open(filename).readlines()]
load_1h = [float(f.split()[3]) for f in open(filename).readlines()]

dates = prescale(dates,15)
temps = prescale(temps,15)
load_15min = prescale(load_15min,15)
load_1h = prescale(load_1h,15)

days = matplotlib.dates.DayLocator()
hours = matplotlib.dates.HourLocator((2,4,6,8,10,12,14,16,18,20,22))
daysFmt = matplotlib.dates.DateFormatter('%d/%m')
hoursFmt  = matplotlib.dates.DateFormatter('%H:00 h')
fig = plt.figure()
ax = fig.add_subplot(111)
ax.plot_date(pylab.date2num(dates), temps, 'b-',label='Temperature')
ax.legend(loc=1)
ax.set_ylabel('Temperature [C]')
ax.set_xlabel('Date')
ax2 = ax.twinx()
#pylab.plot_date(pylab.date2num(dates), load_15min, 'r-', label='Load 15 min')
ax2.plot_date(pylab.date2num(dates), load_1h, 'g-', label='Load 1 h')
ax2.legend(loc=7)
ax2.set_ylabel('load average')
ax.xaxis.set_major_locator(days)
ax.xaxis.set_major_formatter(daysFmt)
ax.xaxis.set_minor_locator(hours)
ax.xaxis.set_minor_formatter(hoursFmt)
ax.autoscale_view()
fig.autofmt_xdate()
labels = ax.get_xmajorticklabels()
pylab.setp(labels, rotation=90, fontsize=10)
labels = ax.get_xminorticklabels()
pylab.setp(labels, rotation=90, fontsize=9)
pylab.savefig('monitoring.png')

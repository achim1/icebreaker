import pylab
import matplotlib
from datetime import datetime

format='%Y/%m/%dT%H:%M:%S'
filename = 'pressure.txt'
dates = [datetime.strptime(f.split()[0],format) for f in open(filename).readlines()]
pressures = [float(f.split()[1]) for f in open(filename).readlines()]

days = matplotlib.dates.DayLocator()
hours = matplotlib.dates.HourLocator((6,12,18))
daysFmt = matplotlib.dates.DateFormatter('%d/%m')
hoursFmt  = matplotlib.dates.DateFormatter('%H:00 h')
fig = pylab.figure()
ax = fig.add_subplot(111)
pylab.plot_date(pylab.date2num(dates), pressures, '-', label='USB stick')
pylab.legend(loc=0)
pylab.ylabel('Pressure [mBar]')
pylab.xlabel('Date')
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
pylab.savefig('pressure.png')

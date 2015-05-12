import pylab
import matplotlib
import datetime
import sys

infile = open(sys.argv[1])
outfilename = sys.argv[2]
dates = []
capacities = []

for line in infile:
    fields = line.split()
    try:
        dates.append(datetime.datetime.strptime(fields[0],'%Y_%m_%d'))
        capacities.append(float(fields[1]))
    except:
        pass

plot = pylab.subplot(111)
line = plot.plot_date(pylab.date2num(dates),capacities,'-')
plot.set_ylim((0,1.1 * max(capacities)))
plot.set_xlabel('Date')
plot.set_ylabel('Disk capacity [GB]')
xaxis = plot.xaxis
date_formatter = matplotlib.dates.DateFormatter('%d/%m')
ndates = len(dates)
if 0 <= ndates <= 10:
    d = 1
elif ndates <= 20:
    d = 2
elif ndates <= 50:
    d = 3
elif ndates <= 100:
    d = 5
elif ndates <= 200:
    d = 10
else:
    d = 20
day_locator = matplotlib.dates.DayLocator(range(1,32,d))
xaxis.set_major_formatter(date_formatter)
xaxis.set_major_locator(day_locator)
labels = xaxis.get_majorticklabels()
for l in labels:
    l.set_rotation('vertical')
    l.set_fontsize(9)
pylab.savefig(outfilename, dpi=75)

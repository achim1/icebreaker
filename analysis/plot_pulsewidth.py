import pylab
import numpy
import bz2
import sys


def main(argv=None):
    if argv is None:
        argv = sys.argv

    filename = argv[1]
    if filename.endswith("bz2"):
        f = bz2.BZ2File(argv[1])
    else:
        f = open(argv[1])
    width_0 = []
    width_1 = []
    width_2 = []
    width_3 = []

    for line in f:
        fields = line.split()
        if len(fields) != 3:
            continue
        w = int(fields[2])
        ch = int(fields[0])
        if w > 0:
            if ch == 0:
                width_0.append(w)
            elif ch == 1:
                width_1.append(w)
            elif ch == 2:
                width_2.append(w)
            elif ch == 3:
                width_3.append(w)

    bins = numpy.linspace(0,200,100)
    dpi = 75
    outdir = sys.argv[2] + '/'
    pylab.hist(width_0,bins=bins)
    pylab.xlabel('Pulse width Channel 0 [ns]')
    pylab.savefig(outdir + 'width_0.png',dpi=dpi)
    pylab.clf()
    pylab.hist(width_1,bins=bins)
    pylab.xlabel('Pulse width Channel 1 [ns]')
    pylab.savefig(outdir + 'width_1.png',dpi=dpi)
    pylab.clf()
    pylab.hist(width_2,bins=bins)
    pylab.xlabel('Pulse width Channel 2 [ns]')
    pylab.savefig(outdir + 'width_2.png',dpi=dpi)
    pylab.clf()
    pylab.hist(width_3,bins=bins)
    pylab.xlabel('Pulse width Channel 3 [ns]')
    pylab.savefig(outdir + 'width_3.png',dpi=dpi)

if __name__ == '__main__':
    main()

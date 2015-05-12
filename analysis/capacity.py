import os
import sys

def capacity(path):
    stat = os.statvfs(path)
    return stat.f_bsize * stat.f_bavail/1024.0**3

def main(argv=None):
    if argv is None:
        argv = sys.argv
    print "%5.2f"%(capacity(argv[1]),)

if __name__ == '__main__':
    main()

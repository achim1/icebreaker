import sys
try:
    import simple_reader
except:
    print "Warning, cythonic simple reader import failed!"
    print "Maybe you shoud recompile"
    import simple_reader_old as simple_reader

simple_reader.analyze_files(sys.argv[1:])

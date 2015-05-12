default: muonfinder PlotTimeDifference

default: tools simple_reader

muonfinder:
	g++ -O2 `root-config --libs --cflags` muonfinder.C -o muonfinder

PlotTimeDifference:
	g++ -O2 `root-config --libs --cflags` PlotTimeDifference.C -o PlotTimeDifference

tools: tools.pyx
	cython tools.pyx
	gcc -Wall -O3 -g -lpython2.6 -I/usr/include/python2.6 -shared tools.c -o tools.so

simple_reader: simple_reader.pyx
	cython simple_reader.pyx
	gcc -Wall -O3 -g -lpython2.6 -I/usr/include/python2.6 -shared simple_reader.c -o simple_reader.so

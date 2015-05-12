LIBUSB_LIB=-lusb-1.0

barometer.so:
	gcc -Wall -c -fPIC barometer.c -o barometer.o
	gcc -shared -Wall ${LIBUSB_LIB} barometer.o -o libbarometer.so

.PHONY: clean
clean:
	rm barometer.o libbarometer.so

cdef class Pulse:

    cdef public bint valid
    cdef bint wait_falling
    cdef int channel
    cdef public double rise_time
    cdef double fall_time

    cpdef rise(self, double time)
    cpdef fall(self, double time)
    cpdef invalidate(self)
    cpdef double width(self)

cdef class MuonFinder:

    cdef object muon
    cdef object muon_callback
    cdef object channels
    cdef double lastpulse_time
    cdef double time_window

    cpdef reset(self)
    cpdef bint coincidence_found(self)
    cpdef analyze_pulse(self, Pulse pulse)

import datetime
import doctest

def datetime2mjd(date, time=None):
    """
    converts a gregorian date to modified julian date
    
    Taken from Enno Middelbergs webpage on astronomy scripts at
    http://www.atnf.csiro.au/people/Enno.Middelberg/python/python.html
    >>> datetime2mjd("27.3.2009")
    54917.5
    >>> datetime2mjd(datetime.datetime(1973,5,14))
    41816.5
    """

    if isinstance(date, datetime.date):
        dd = date.day
        mm = date.month
        yyyy = date.year
    elif isinstance(date, str):
        date=date.split(".")
        dd=int(date[0])
        mm=int(date[1])
        yyyy=int(date[2])

    if isinstance(time, datetime.time):
        hh = time.hour
        min = time.minute
        sec = time.second
    elif isinstance(time, str):
        time=time.split(":")
        hh=int(time[0])
        min=int(time[1])
        sec=int(time[2])
    else:
        hh = 12
        min = 0
        sec = 0

    UT=hh + min/60.0 + sec/3600.0

    if (100*yyyy+mm-190002.5)>0:
        sig=1
    else:
        sig=-1

    JD = 367*yyyy - int(7*(yyyy+int((mm+9)/12))/4) + int(275*mm/9) + dd + 1721013.5 + UT/24 - 0.5*sig +0.5
    MJD = JD - 2400000.5
    return MJD

def mjd2datetime(mjd):
    """
    Convert an MJD to a gregorian datetime.datetime object

    >>> mjd2datetime(54917.5)
    datetime.datetime(2009, 3, 27, 12, 0)
    >>> mjd2datetime(41816.0)
    datetime.datetime(1973, 5, 14, 0, 0)
    """
    jd = mjd + 2400000.5
    jd=jd+0.5
    Z=int(jd)
    F=jd-Z
    alpha=int((Z-1867216.25)/36524.25)
    A=Z + 1 + alpha - int(alpha/4)

    B = A + 1524
    C = int( (B-122.1)/365.25)
    D = int( 365.25*C )
    E = int( (B-D)/30.6001 )

    dd = B - D - int(30.6001*E) + F

    if E<13.5:
        mm=E-1

    if E>13.5:
        mm=E-13

    if mm>2.5:
        yyyy=C-4716

    if mm<2.5:
        yyyy=C-4715

    h=int((dd-int(dd))*24)
    min=int((((dd-int(dd))*24)-h)*60)
    sec=86400*(dd-int(dd))-h*3600-min*60
   
    return datetime.datetime(yyyy,mm,int(dd),h,min,int(sec))

if __name__ == '__main__':
    doctest.testmod()

import sys
import re
from average import AverageRate as Average
from datetime import datetime
from tools import time_to_seconds

psdattelegrampattern = re.compile(r"(?P<head>.[a-zA-Z]+),(?P<time>[0-9.]+),(?P<date>[0-9.]+),(?P<latitude>[0-9.]+),(?P<nshem>N|S),(?P<longitude>[0-9.]+),(?P<ewhem>E|W),(?P<pressure>[0-9.]+),(?P<temperature>[0-9.]+),(?P<ceiling>[0-9.]+),(?P<globradiation>[0-9.]+),(?P<precipitation>[0-9.]+),(?P<humidity>[0-9.]+),(?P<visibility>[0-9.]+)*(?P<NMEA>[0-9a-zA-Z.]+)")

#helpers
def compile_result(mediandata,averages):
    resultstr = ""
    resultstr += mediandata["data"].strftime("%Y/%m/%d %H:%M:%S") 
    resultstr += ";"
    resultstr += mediandata["lat"]
    resultstr += mediandata["nshem"]
    resultstr += ";"
    resultstr += mediandata["lon"]
    resultstr += mediandata["ewhem"]
    resultstr += ";"
    for key in sorted(averages.keys()):
        resultstr += averages[key]
        resultstr += ";"
    return resultstr  

class AverageValueContainer(object):
    
    def __init__(self,interval):
        
        self.pressure      = Average(interval) 
        self.temperature   = Average(interval)
        self.ceiling       = Average(interval) 
        self.globradiation = Average(interval)  
        self.precipitation = Average(interval)    
        self.humidity      = Average(interval)   
        self.visibility    = Average(interval)    
    def add_values(self,dicti,thetime):
       self.pressure.put(thetime,weight =float(dicti["pressure"]))      
       self.temperature.put(thetime,weight = float(dicti["temperature"]))  
       self.ceiling.put(thetime,weight = float(dicti["ceiling"]))      
       self.globradiation.put(thetime,weight = float(dicti["globradiation"]))
       self.humidity.put(thetime,weight = float(dicti["humidity"]))     
       self.visibility.put(thetime,weight = float(dicti["visibility"]))

    def averages(self):
        averages = dict()
        for key in self.__dict__.keys():# ["pressure","temperature","ceiling","globradiation","humidity","visibility"]:
            averages[key] = self.__getattribute__(key).avg()
        return averages
            
    def reset(self):
        bin_start = self.temperature.bin_start
        averages  = self.averages()
        for key in self.__dict__.keys():
            self.__getattribute__(key).reset() 

        return bin_start,averages

def datetimer(date,time):
    h = int(time[:2])
    m = int(time[2:4])
    s = int(time[4:6])
    d = int(date[:2])
    m = int(date[2:4])
    y = int(date[4:8])
    return datetime(y,m,d,h,m,s)

infilename = sys.argv[1]
averagecont = AverageValueContainer(3600)
mediancontainer = []
with open(infilename,"r") as f:
    #first print field information
    print "#"+"date,lat,lon," + ",".join(sorted(averagecont.__dict__.keys()))
    for line in f.xreadlines():
        pat = psdattelegrampattern.search(line)
        if pat is None:
            continue
        else:
            data = pat.groupdict()
            try:
                thedate = datetimer(data["date"],data["time"])
            except Exception as e:
                continue
            pos_dict = dict()
            pos_dict["date"] = thedate
            pos_dict["lat"]  = data["latitude"]
            pos_dict["lon"]  = data["longitude"]
            pos_dict["nshem"] = data["nshem"]
            pos_dict["ewhem"] = data["ewhem"]
            mediancontainer.append(pos_dict)
            try:
		thetime = time_to_seconds(data["time"],"000")
                averagecont.add_values(data,thetime)
            except ValueError as e:
		print e
                bin_start,averages = averagecont.reset()
                medianindex = int(len(mediancontainer)/2.)                
                mediandata = mediancontainer[medianindex]
                result = compile_result(mediandata,averages)
                print result








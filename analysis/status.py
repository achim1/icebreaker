import sys
import datetime
import os
import capacity
import subprocess


# ensure these variables are defined by sourcing
# config.sh first
# if problems, change there
SDCARD_PATH=os.getenv("SDCARD_PATH")
DATA_PATH=os.getenv("DATA_BASEDIR")
ICEBREAKER_PATH=os.getenv("ICEBREAKER_DIR")
ROOT_PATH="/"

#if you change here, you might have to change scripts
ANALYSIS_PATH=DATA_PATH + "/analysis"
LOAD=ICEBREAKER_PATH + "/analysis/load.sh"
CPUTMP=ICEBREAKER_PATH + "/analysis/cpu_temp.sh"
UPTIME=ICEBREAKER_PATH + "/analysis/uptime.sh"
MEMFREE=ICEBREAKER_PATH + "/analysis/memfree.sh"

try:
    capacity_sdcard = capacity.capacity(SDCARD_PATH)
except OSError:
    capacity_sdcard = -42.0
error_limit_sdcard = 1.0

capacity_data = capacity.capacity(DATA_PATH)
error_limit_data = 1.0

capacity_root = capacity.capacity(ROOT_PATH)
error_limit_root = 0.5

out = open('index.html','w')
template = open('template.html').read()

if capacity_data > error_limit_data:
    data_mode = 'fine'
else:
    data_mode = 'error'

if capacity_sdcard < 0:
    sdcard_mode = "n.a."
elif capacity_sdcard > error_limit_sdcard:
    sdcard_mode = 'fine'
else:
    sdcard_mode = 'error'

if capacity_root > error_limit_root:
    root_mode = 'fine'
else:
    root_mode = 'error'

try:
    temp = int(subprocess.Popen([CPUTMP], stdout=subprocess.PIPE).communicate()[0])
except ValueError:
    temp = -42.0
if temp < 0:
    temp_mode = "n.a."
elif temp > 70:
    temp_mode = 'error'
else:
    temp_mode = 'fine'
try:
    load = float(subprocess.Popen([LOAD], stdout=subprocess.PIPE).communicate()[0])
except ValueError:
    load = -42.0

if load < 0:
    load_mode = "n.a."
if load > 7.0:
    load_mode = 'error'
else:
    load_mode = 'fine'

try:
    memfree = float(subprocess.Popen([MEMFREE], stdout=subprocess.PIPE).communicate()[0])
    memfree = memfree/1024
except ValueError:
    memfree = -42.0

if memfree < 0:
    mem_mode = "n.a."
if memfree < 100 :
    mem_mode = 'error'
else:
    mem_mode = 'fine'
uptime = subprocess.Popen([UPTIME], stdout=subprocess.PIPE).communicate()[0]
if uptime is None:
    uptime = -42.

daq_dir = DATA_PATH + '/daq'
pressure_dir = DATA_PATH + '/pressure'

today  = datetime.datetime.utcnow()
one_day = datetime.timedelta(1)
yesterday = today - one_day
yesterdays_daq_dir = datetime.datetime.strftime(yesterday,'/%Y/%m/%d')
todays_daq_dir = datetime.datetime.strftime(today,'/%Y/%m/%d')
today_full_string = datetime.datetime.strftime(today,'%Y/%m/%dT%H:%M:%S')
today_string = datetime.datetime.strftime(today,'%Y/%m/%d')
yesterday_string = datetime.datetime.strftime(yesterday,'%Y/%m/%d')

todays_daq_file_list = os.listdir(daq_dir+todays_daq_dir)
todays_daq_file_list.sort()
yesterdays_daq_file_list = os.listdir(daq_dir+yesterdays_daq_dir)
yesterdays_daq_file_list.sort()
todays_daq_files = len(todays_daq_file_list)
yesterdays_daq_files = len(yesterdays_daq_file_list)
hour = today.hour
if todays_daq_files < hour+1 or todays_daq_files > 50:
    todays_daq_mode = 'error'
else:
    todays_daq_mode = 'fine'
if yesterdays_daq_files > 50 or yesterdays_daq_files < 23:
    yesterdays_daq_mode = 'error'
else:
    yesterdays_daq_mode = 'fine'

if todays_daq_files == 1:
    last_finished_daqfile = yesterdays_daq_file_list[-1]
    last_finished_daqfile_size = os.path.getsize(daq_dir+yesterdays_daq_dir+'/'+last_finished_daqfile)
else:
    last_finished_daqfile = todays_daq_file_list[-2]
    last_finished_daqfile_size = os.path.getsize(daq_dir+todays_daq_dir+'/'+last_finished_daqfile)
last_finished_daqfile_size = last_finished_daqfile_size/(1024.0*1024.0)
last_finished_daqfile_mtime = datetime.datetime.utcfromtimestamp(os.path.getmtime(daq_dir+todays_daq_dir+'/'+last_finished_daqfile))
last_finished_daqfile_age = today - last_finished_daqfile_mtime
last_finished_daqfile_age = last_finished_daqfile_age.days * 86400 + last_finished_daqfile_age.seconds

if last_finished_daqfile_age > 3600.0:
    last_finished_daqfile_age_mode = 'error'
else:
    last_finished_daqfile_age_mode = 'fine'

if 0.8 < last_finished_daqfile_size < 4.0:
    last_finished_daqfile_mode = 'fine'
else:
    last_finished_daqfile_mode = 'error'

total_amount_data_yesterday = 0.
total_amount_data_today = 0.
for f in todays_daq_file_list[:-1]:
    total_amount_data_today += os.path.getsize(daq_dir+todays_daq_dir+'/'+f)
total_amount_data_today = total_amount_data_today/(1024.0 * 1024.0)
for f in yesterdays_daq_file_list:
    total_amount_data_yesterday += os.path.getsize(daq_dir+yesterdays_daq_dir+'/'+f)
total_amount_data_yesterday = total_amount_data_yesterday/(1024.0 * 1024.0)
if 0.8 * 24 < total_amount_data_yesterday < 4.0 * 24:
    total_amount_data_yesterday_mode = 'fine'
else:
    total_amount_data_yesterday_mode = 'error'
if 0.8 * hour < total_amount_data_today < 4.0 * hour:
    total_amount_data_today_mode = 'fine'
else:
    total_amount_data_today_mode = 'error'


#todays_inclination_file_list = os.listdir(inclination_dir+todays_daq_dir)
#yesterdays_inclination_file_list = os.listdir(inclination_dir+yesterdays_daq_dir)
#todays_inclination_file_list.sort()
#yesterdays_inclination_file_list.sort()
#todays_inclination_files = len(todays_inclination_file_list)
#yesterdays_inclination_files = len(yesterdays_inclination_file_list)
#if todays_inclination_files < hour+1 or todays_inclination_files > 50:
#    todays_inclination_mode = 'error'
#else:
#    todays_inclination_mode = 'fine'
#if yesterdays_inclination_files > 50 or yesterdays_inclination_files < 23:
#    yesterdays_inclination_mode = 'error'
#else:
#    yesterdays_inclination_mode = 'fine'
#if todays_inclination_files == 1:
#    last_finished_inclinationfile = yesterdays_inclination_file_list[-1]
#    last_finished_inclinationfile_size = os.path.getsize(inclination_dir+yesterdays_daq_dir+'/'+last_finished_inclinationfile)
#else:
#    last_finished_inclinationfile = todays_inclination_file_list[-2]
#    last_finished_inclinationfile_size = os.path.getsize(inclination_dir+todays_daq_dir+'/'+last_finished_inclinationfile)
#last_finished_inclinationfile_size = last_finished_inclinationfile_size/1024.0
#last_finished_inclinationfile_mtime = datetime.datetime.utcfromtimestamp(os.path.getmtime(inclination_dir+todays_daq_dir+'/'+last_finished_inclinationfile))
#last_finished_inclinationfile_age = today - last_finished_inclinationfile_mtime
#last_finished_inclinationfile_age = last_finished_inclinationfile_age.days * 86400 + last_finished_inclinationfile_age.seconds

#if last_finished_inclinationfile_age > 3600.0:
#    last_finished_inclinationfile_age_mode = 'error'
#else:
#    last_finished_inclinationfile_age_mode = 'fine'

#if 10.0 < last_finished_inclinationfile_size < 30.0:
#    last_finished_inclinationfile_mode = 'fine'
#else:
#    last_finished_inclinationfile_mode = 'error'

# We have no inclination sensor on the second Polarstern voyage
last_finished_inclinationfile_mode = 'fine'
last_finished_inclinationfile_age_mode = 'fine'
todays_inclination_mode = 'fine'
yesterdays_inclination_mode = 'fine'
last_finished_inclinationfile_size = 0.
todays_inclination_files = 0
yesterdays_inclination_files = 0
last_finished_inclinationfile_age = 0.
last_finished_inclinationfile = ''

try:
    todays_pressure_files = len(os.listdir(pressure_dir+todays_daq_dir))
except OSError,ValueError:
    todays_pressure_files = 0
try:
    yesterdays_pressure_files = len(os.listdir(pressure_dir+yesterdays_daq_dir))
except OSError,ValueError:
    yesterdays_pressure_files = 0

if todays_pressure_files != 1:
    todays_pressure_mode = 'error'
else:
    todays_pressure_mode = 'fine'
if yesterdays_pressure_files != 1:
    yesterdays_pressure_mode = 'error'
else:
    yesterdays_pressure_mode = 'fine'

muonratefile = open(ANALYSIS_PATH +'/status/muonrates.txt')
for line in muonratefile:
    data = line
fields = data.split()
yesterdays_muon_date = fields[0].replace('_','/')
yesterdays_muon_rate = float(fields[1])/86400
if yesterdays_muon_rate < 0.3 or yesterdays_muon_rate > 1.0:
    muon_mode = 'error'
else:
    muon_mode = 'fine'

outhtml = template%(today_full_string,
                    yesterdays_daq_dir,
                    yesterdays_muon_date, muon_mode, yesterdays_muon_rate,
                    last_finished_daqfile, last_finished_daqfile_mode, last_finished_daqfile_size,
                    last_finished_daqfile,last_finished_daqfile_age_mode,last_finished_daqfile_age,
                    today_string,total_amount_data_today_mode,total_amount_data_today,
                    yesterday_string,total_amount_data_yesterday_mode,total_amount_data_yesterday,
                    today_string,todays_daq_mode,todays_daq_files,
                    yesterday_string,yesterdays_daq_mode,yesterdays_daq_files,
                    today_string,todays_inclination_mode,todays_inclination_files,
                    yesterday_string,yesterdays_inclination_mode,yesterdays_inclination_files,
                    last_finished_inclinationfile, last_finished_inclinationfile_mode, last_finished_inclinationfile_size,
                    last_finished_inclinationfile,last_finished_inclinationfile_age_mode,last_finished_inclinationfile_age,
                    today_string, todays_pressure_mode,todays_pressure_files,
                    yesterday_string, yesterdays_pressure_mode, yesterdays_pressure_files,
                   sdcard_mode, capacity_sdcard,
                    data_mode, capacity_data,
                   root_mode, capacity_root,
                   temp_mode, temp,
                   load_mode, load,
                   mem_mode, memfree,
                   uptime)

out.write(outhtml)

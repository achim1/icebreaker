
IceBreaker - V2.0 "Polaris"
====================================

A sleek and easy-to-use focused release of Robert Franke's icebreaker with enhanced analysis support.

Changelog
------------

* Removed inclination detector support
* Removed server 
* Fixed average.py
* all paths used for the analysis scripts are now found in analysis/config.sh, which defines the paths as variables and thus might need to be sourced
* However, it is still needed to check the paths in icebreaker.py and barometer.py
* fixed the generation of the status webpage
* reworked the analysis.sh script. It is now more sleek and easier to read. Unused features have been removed
* don't fail if the barometer does not work

Files and directories
-------------------------
data dir:
A single dir for the rawdata and pre-analyzed data is recommended - structured like this:

rawdata (datadir) 
 |_ analysis
 |_ daq 
 |_ pressure
 

Crontab
------------------
analysis/analysis.sh and analysis/send_report.sh need crontab entries to be executed each day

if data should be back-up'd another crontab entry is recommended

Setup
--------------

icebreaker.py and barometer.py both have to run via the python daemon library.
To do so, the service architecture of ubuntu is invoked

You can start services with:
sudo service daq start

That this works, the script "daq" has to be in the /etc/init.d/ folders. This is taken care of by icebreaker/daq/setup_boot.sh and similar for the barometer by icebreaker/barometer/setup_boot.sh

A temporary folder needs to exist and has to be given in analysis/config.sh



known issues
---------------

- Rechner bootet nicht sauber durch, wenn Barometer angesteckt ist (Kernel wirft Fehler wenn er versucht das USB Device zu resetten)
    Loesung: Batterie erneuern?
- USB-Stick und SD-Karte mit ext3 formatieren -> Done

- libbarometer.so Pfad konfigurierbar machen -> Done
- Wie macht man einen ordentlichen Daemon? -> Done
- Upstartintegration? ->Done
- Logfile Rotation Period auf 1 Tag aendern! -> Done

- Time synchronization with NTP -> Done, /etc/cron.daily/ntpdate
- Plotting in cron job with matplotlib didn't work because it couldn't find the DISPLAY
  -> Solved, changed backend to Agg in /etc/matplotlibrc, interactive to false

Polarstern 2011
---------------

- We are going to run without an inclination sensor, thus remove it from analysis
- Muon extraction doesn't work, fix...

Polarstern 2011/2011
--------------------

- We are going to run without the usb stick, thus remove it from crontab (synching) and fstab



#!/usr/bin/env bash

# simple analyzing script 
# prepares email payload

# config defines the paths, if problems
# change that file accordingly
# unfortunately full path is needed as this script
# will be executed by cron

source $HOME/icebreaker/analysis/config.sh
# don't change, or you might have to change the scripts
ANALYSIS_BASEDIR=${DATA_BASEDIR}/analysis
DAQ_BASEDIR=${DATA_BASEDIR}/daq
PRESSURE_BASEDIR=${DATA_BASEDIR}/pressure
DSHIP_BASEDIR=${DATA_BASEDIR}/dship
MUON_HISTORY=$ANALYSIS_BASEDIR/status/muonrates.txt
MUON_PLOT=$ANALYSIS_BASEDIR/status/muonrate.png
CAPACITY_SDCARD=$ANALYSIS_BASEDIR/status/capacity_sdcard.txt
CAPACITY_SDCARD_PLOT=$ANALYSIS_BASEDIR/status/capacity_sdcard.png
CAPACITY_DATA=$ANALYSIS_BASEDIR/status/capacity_data.txt
CAPACITY_DATA_PLOT=$ANALYSIS_BASEDIR/status/capacity_data.png
YESTERDAYS_DAQ_DATE_DIR=`python ${ICEBREAKER_DIR}/analysis/yesterday.py`
YESTERDAYS_DAQ_DIR=$DAQ_BASEDIR/$YESTERDAYS_DAQ_DATE_DIR
OUTPUTFILENAME=`echo $YESTERDAYS_DAQ_DATE_DIR | sed 's/\//_/g'`
OUTPUTDIR=$ANALYSIS_BASEDIR/$YESTERDAYS_DAQ_DATE_DIR
MUONOUTPUTFILE=$OUTPUTDIR/muon_$OUTPUTFILENAME
#PULSEOUTPUTFILE=$OUTPUTDIR/pulses_$OUTPUTFILENAME
GPSOUTPUTFILE=$OUTPUTDIR/gps.dat
STATUS=${ICEBREAKER_DIR}/analysis/status.sh

# make sure the outputdir exists and is empty
mkdir -p $OUTPUTDIR
#rm -f $OUTPUTDIR/send/*
#rmdir $OUTPUTDIR/send/
rm -rf $OUTPUTDIR/*
touch $MUONOUTPUTFILE
#touch $PULSEOUTPUTFILE
touch $GPSOUTPUTFILE

# make sure the statusdir exists
mkdir -p $ANALYSIS_BASEDIR/status
touch MUONHISTORY
touch CAPACITY_SDCARD
touch CAPACITY_DATA

# prepare the tmpfile
rm -f $TMPFILE


# computer status
$STATUS

# analyze the hourly written daqfiles
for file in `ls $YESTERDAYS_DAQ_DIR`;
do
    FULL_FILENAME=$YESTERDAYS_DAQ_DIR/$file
    nice -n 19 python ${ICEBREAKER_DIR}/analysis/analyze_file.py $FULL_FILENAME > $TMPFILE
    cat $TMPFILE | grep -e "MUON" -e "Error" | sed 's/MUON[[:space:]]*//' >> $MUONOUTPUTFILE
#    cat $TMPFILE | grep -e "^p" -e "Error" | sed 's/^p[[:space:]]*//' >> $PULSEOUTPUTFILE
    bzcat $FULL_FILENAME | grep -A 11 DG >> $GPSOUTPUTFILE
done
rm $TMPFILE

# copy the pressure files if any
for file in $PRESSURE_BASEDIR/$YESTERDAYS_DAQ_DATE_DIR/*;
do
    touch $OUTPUTDIR/press_`basename $file`
    cp $file $OUTPUTDIR/press_`basename $file`
done
# copy the dship files if any
for file in $DSHIP_BASEDIR/$YESTERDAYS_DAQ_DATE_DIR/*;
do
    touch $OUTPUTDIR/dship_`basename $file`
    cp $file $OUTPUTDIR/dship_`basename $file`
done


# prevent tar errors by ensuring that every file is created
touch $OUTPUTDIR/daq.log
touch $OUTPUTDIR/barometer.log
# send only the last 500 (50) lines of the log files by mail to avoid
# large mails due to continuous errors
tail -n 500 ${ICEBREAKER_DIR}/daq/daq.log > $OUTPUTDIR/daq.log
tail -n 50 ${ICEBREAKER_DIR}/barometer/barometer.log > $OUTPUTDIR/barometer.log

python ${ICEBREAKER_DIR}/analysis/average.py $MUONOUTPUTFILE $COINCIDENCE_LEVEL > $OUTPUTDIR/rate_averages

# Now record some date for plots
NMUONS=`grep -v Error -c $MUONOUTPUTFILE`
echo $OUTPUTFILENAME
echo $NMUONS
echo $MUON_HISTORY
echo $OUTPUTFILENAME $NMUONS >> $MUON_HISTORY
python ${ICEBREAKER_DIR}/analysis/plot_muonrate.py $MUON_HISTORY $MUON_PLOT

#echo $OUTPUTFILENAME `python /home/cosmic/icebreaker/analysis/capacity.py /media/data/` >> $CAPACITY_DATA
#echo $OUTPUTFILENAME `python /home/cosmic/icebreaker/analysis/capacity.py /media/sdcard/` >> $CAPACITY_SDCARD
#python /home/cosmic/icebreaker/analysis/plot_capacity.py $CAPACITY_DATA $CAPACITY_DATA_PLOT
#python /home/cosmic/icebreaker/analysis/plot_capacity.py $CAPACITY_SDCARD $CAPACITY_SDCARD_PLOT
#python /home/cosmic/icebreaker/analysis/plot_pulsewidth.py $PULSEOUTPUTFILE $ANALYSIS_BASEDIR/status

wget -O $OUTPUTDIR/status.html localhost/index.html

# Now we can create the tarballs
mkdir -p $OUTPUTDIR/send
cd $OUTPUTDIR
tar --create -j --ignore-command-error -f $OUTPUTDIR/send/polarstern_filtered_$OUTPUTFILENAME.tar.bz2 *.log press_* muon_* gps.dat dship_* status.html rate_averages

#bzip2 -9 $PULSEOUTPUTFILE
bzip2 -9 $MUONOUTPUTFILE

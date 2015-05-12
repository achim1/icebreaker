#!/usr/bin/env bash

# configfile defines paths and recipients
# if problems, check this file
# unfortunately the full path here is needed
# instead of the relative path
# as this script needs to be executed by cron
source /home/cosmic/icebreaker/analysis/config.sh

MAILFILE=/tmp/mail
SUBJECTFILE=/tmp/subject
DATETIME=`date`
DATE=`date +%Y-%m-%d`
YESTERDAY=`python ${ICEBREAKER_DIR}/analysis/yesterday.py`
YESTERDAY_UNDERSCORES=`echo $YESTERDAY | sed 's/\//_/g'`

touch $MAILFILE
touch $SUBJECTFILE

# This is necessary to support blanks and '-' in the subject line
echo "Polarstern -- Status Report" > $SUBJECTFILE
echo $YESTERDAY
echo $DATE
echo $DATETIME


echo "Status Report - $DATETIME" > $MAILFILE
echo -e "\n" >> $MAILFILE
echo -e "\n" >> $MAILFILE
echo ""  >> $MAILFILE
echo "In the attachment you will find the status.html file" >> $MAILFILE

python ${ICEBREAKER_DIR}/analysis/sendmail.py $SUBJECTFILE $MAILFILE $RECIPIENTS ${DATA_BASEDIR}/analysis/$YESTERDAY/send/polarstern_filtered_${YESTERDAY_UNDERSCORES}.tar.bz2
# If you wanted to attach pictures or zip etc. do like this
# $SCRIPTDIR/sendmail.py $SUBJECTFILE $MAILFILE $RECIPIENTS file1 file2 file3

rm $MAILFILE

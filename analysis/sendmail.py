#!/usr/bin/env python

import sys
from os.path import basename
import smtplib
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

usage='Usage: sendmail.py subject-file message-file recipients [attachment image files]'

if len(sys.argv)<3:
    print usage
    sys.exit(1)

server_address='134.1.100.1'
from_address='desydata@fs-polarstern.de'

COMMASPACE=", "
recipients = sys.argv[3].split(",")

# Create the container (outer) email message.
msg = MIMEMultipart()
msg['Subject'] = open(sys.argv[1]).read()
msg['From'] = from_address
msg['To'] = COMMASPACE.join(recipients)

fp = open(sys.argv[2], 'rb')
# Create a text/plain message
text = MIMEText(fp.read())
fp.close()
msg.attach(text)

for filename in sys.argv[4:]:
    # Open the files in binary mode.  MIMEText class for .html file
    fp = open(filename, 'rb')
    if filename.endswith("html") or filename.endswith("txt"):
        img = MIMEText(fp.read())
    elif filename.endswith("png") or filename.endswith("jpg"):
        img = MIMEImage(fp.read())
    else:
        img = MIMEApplication(fp.read())
    fp.close()
    img.add_header('content-disposition', 'attachment', filename=basename(filename))
    msg.attach(img)

server = smtplib.SMTP(server_address)

try:
    server.sendmail(from_address,recipients,msg.as_string())
except:
    print "Sending of mesage  failed"
    sys.exit(1)
finally:
    server.quit()

print "Message successfully sent"

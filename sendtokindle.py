# -*- coding: utf-8 -*- 
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email import encoders
import smtplib
import os
import logging
import urllib
logging.basicConfig()
logger=logging.getLogger('qikan.sendToKindle')
def send(ebook,sender,to,smtp,username,password):   
    outer = MIMEMultipart()
    outer['Subject'] = os.path.basename(ebook)
    outer['To'] = to
    outer['From'] = sender
    outer.preamble = 'You will not see this in a MIME-aware mail reader.\n'
    ctype = 'application/x-mobipocket-ebook'
    maintype, subtype = ctype.split('/', 1)
    fp = open(ebook, 'rb')
    msg = MIMEBase(maintype, subtype)
    msg.set_payload(fp.read())
    fp.close()
    encoders.encode_base64(msg)
    msg.add_header('Content-Disposition', 'attachment', filename=('utf-8', '', os.path.basename(ebook).encode('utf-8') ))
    outer.attach(msg)
    composed = outer.as_string()
    logger.debug('send %s to kindle',ebook)
    s = smtplib.SMTP(smtp)
    logger.debug('connect to %s' % smtp)
    s.login(username,password)
    logger.debug('login OK')
    s.sendmail(sender, to, composed)
    logger.debug('send OK')
    s.quit()

def main():
    logging.getLogger().setLevel(logging.DEBUG)
    

if __name__ == '__main__':
    main()        
# -*- coding: utf-8 -*- 
from downloadqikan import QiKanDownloader
import mobi
import logging
import sendtokindle
import config
import sys, traceback
#define belows in config.py
#magazines
#qikanUsername
#qikanPassword
#mailSender
#mailTo
#mailSmtpServer
#mailUsername
#mailPassword
def main():
    logging.getLogger('qikan').setLevel(logging.DEBUG)
    magazines=config.magazines
    downloader = QiKanDownloader()
    try:
        downloader.login(config.qikanUsername,config.qikanPassword)
        for m in magazines:
            try:
                magazine=downloader.download(m)
                if (magazine):
                    mobifile=mobi.convert(magazine.getEpubPath())
                    if (mobifile):
                        sendtokindle.send(mobifile,config.mailSender,config.mailTo,config.mailSmtpServer,config.mailUsername,config.mailPassword)   
                        print "done"
            except Exception as inst:                
                traceback.print_exc(file=sys.stdout)
                

    finally:
        downloader.quit()


if __name__ == '__main__':
    main()
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
    downloader = QiKanDownloader()
    try:
        downloader.login(config.qikanUsername,config.qikanPassword)
        for m in ['http://www.qikan.com.cn/MagDetails/1671-2145/2013/1.html']:
            magazine=downloader.downloadDetail(m)
            if (magazine):
                mobifile=mobi.convert(magazine.getEpubPath())
                if (mobifile):
                    sendtokindle.send(mobifile,config.mailSender,config.mailTo,config.mailSmtpServer,config.mailUsername,config.mailPassword)   
                    print "done"

                

    finally:
        downloader.quit()


if __name__ == '__main__':
    main()
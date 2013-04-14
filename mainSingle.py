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
        m = 'http://www.qikan.com.cn/MagDetails/1008-5017/2013/12.html'        
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
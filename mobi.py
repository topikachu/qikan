# -*- coding: utf-8 -*-
import logging
logging.basicConfig()
logger=logging.getLogger('qikan.mobi')
from subprocess import call
import os
def convert(source):
    root,ext=os.path.splitext(source)
    dest=root+'.mobi'
    logger.debug('convert %s to %s' %(source,dest))
    call (['ebook-convert.exe',source.encode('mbcs'),dest.encode('mbcs')])
    if (os.path.isfile(dest)):
        return dest    


def main():
    convert(u'C:\\pikachu\\git\\qikan\\workspace\\读者2013年第7期.epub')


if __name__ == '__main__':
    main()
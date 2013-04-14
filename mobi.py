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
    call (['ebook-convert.exe',source.encode('gb18030'),dest.encode('gb18030')])
    if (os.path.isfile(dest)):
        return dest    

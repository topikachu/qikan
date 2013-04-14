# -*- coding: utf-8 -*-  
from splinter import Browser

import logging
import datetime
import uuid
from mako.template import Template
import os
import codecs
import shutil
import zipfile
import urllib2

logging.basicConfig()
logger=logging.getLogger('qikan.Dowloader')


class Saver():
    def __init__(self,magazine):
        self.magazine=magazine
    def saveUTF8(self,filename,content,):
        f=codecs.open(os.path.join(self.magazine.destFolder(),filename),'w','utf-8')
        f.write(content)
        f.close()


class Magazine(Saver):
    opfT=Template(filename='template/content.opf',input_encoding='utf-8')
    tocT=Template(filename='template/toc.ncx',input_encoding='utf-8')
    indexT=Template(filename='template/index.html',input_encoding='utf-8')
    def __init__(self):
        self.sections=[]
        Saver.__init__(self,self)
        self.creationTime=datetime.date.today().isoformat()
        self.uuid=str(uuid.uuid1())

    def destFolder(self):
        return os.path.join('workspace',self.name+self.description)

    def preSave(self):
        idx=1
        self.sections=[s for s in self.sections if len(s.articles)]
        for s in self.sections:
            if not s.name:
                s.name="Section" 
            s.location="section%d.html" % idx
            s.id="id%d" % idx
            idx=idx+1
            for a in s.articles:
                a.location="article%d.html" % idx
                a.id="id%d" % idx
                idx=idx+1
        dest=self.destFolder()
        if (os.path.isdir(dest)):
            shutil.rmtree(dest, ignore_errors=True)
        shutil.copytree('template',dest)
        logger.debug("prepare target folder %s" % dest)
    def saveEpubMetadata(self):        
        self.saveUTF8('content.opf',Magazine.opfT.render_unicode(magazine=self))                
        self.saveUTF8('toc.ncx',Magazine.tocT.render_unicode(magazine=self))
        logger.debug('save epub metadata')

    def saveIndex(self):
        self.saveUTF8('index.html',Magazine.indexT.render_unicode(magazine=self))

    def getEpubPath(self):
        return self.destFolder()+'.epub'
    def genEpub(self):
        if (self.cover):            
            req=urllib2.Request(self.cover)
            req.add_header("Referer",self.url)
            r=urllib2.urlopen(req)
            f=open(os.path.join(self.destFolder(),"cover.jpg"),"wb")
            f.write(r.read())
            f.close()            
        zip = zipfile.ZipFile(self.getEpubPath(), 'w')    
        for root, dirs, files in os.walk(self.destFolder()):
            for f in files:
                zip.write(os.path.join(root, f),os.path.join(root[len(self.destFolder()):],f))
        zip.close()



        
class Section(Saver):
    sectionT=Template(filename='template/section.html',input_encoding='utf-8')
    def __init__(self,magazine):
        self.articles=[]
        Saver.__init__(self,magazine)

    def save(self):        
        self.saveUTF8(self.location,Section.sectionT.render_unicode(section=self))
        logger.debug('save section %s' % self.name)

class Article(Saver):
    articleT=Template(filename='template/article.html',input_encoding='utf-8')
    def __init__(self,section,magazine):
        self.urls=[]
        self.section=section
        self.magazien=magazine
        Saver.__init__(self,magazine)
    def save(self):        
        self.saveUTF8(self.location,Article.articleT.render_unicode(article=self),)
        logger.debug('save article %s' % self.name)

class QiKanDownloader():
    def __init__ (self):
        self.browser=Browser(profile='C:/Users/pikachu/AppData/Roaming/Mozilla/Firefox/Profiles/odfwln6i.default')
        #self.browser=Browser(driver_name='phantomjs',load_images=False,wait_time=10)
        #self.browser=Browser(driver_name='chrome')
        #self.browser=Browser(driver_name='zope.testbrowser')
        
    def login(self,username,password):
        logger.debug('login start')
        browser=self.browser
        browser.visit('http://www.qikan.com.cn/userrelative/login.aspx?backurl=http%3A//www.qikan.com.cn/') 
        browser.find_by_id('ctl00_ContentDefault_txtUserName').first.fill(username)
        browser.evaluate_script("ctl00_ContentDefault_txtPwd.value='%s'" % password)
        browser.find_by_css('div.btn_login>input').first.click() 
        logger.debug('login finish')
    
    def download(self,magazine):
        import time
        time.sleep(2)
        logger.debug('dowload %s' % magazine)
        browser=self.browser
        browser.visit(magazine)
        detail=browser.find_by_css('a.all_v1')
        if (len(detail)):
            logger.debug('has detail')
            return self.downloadDetail()
        else:
            logger.debug('no detail')
    def downloadDetail(self):        
        logger.debug('detail download start')
        browser=self.browser
        detail=browser.find_by_css('a.all_v1')
        if (len(detail)==0):
            logger.debug("no detail page")
            return
        magazine=Magazine()
        detailUrl=detail.first['href']
        logger.debug('go to detail page')
        magazine.url=detailUrl
        browser.visit(detailUrl)
        magazine.name=browser.find_by_css('span.magName').first.text
        logger.debug('mag name is %s' % magazine.name)
        magazine.description=browser.find_by_css('span.magDate').first.text
        logger.debug('mag description is %s' % magazine.description)
        coverElement=browser.find_by_css('img#imgCoverImage')
        if (len(coverElement)):
            magazine.cover=coverElement.first['src']
            logger.debug('mag cover is %s' % magazine.cover)

        articleElements=browser.find_by_css('div.magDetails_con_l>*')
        
        articles=[]
        for e in articleElements:            
            if e.tag_name.lower()=='h1':
                section=Section(magazine)
                section.name=e.text
                magazine.sections.append(section)
                logger.debug('found section %s' % section.name)
            else:
                if ('section' not in vars()):
                    section=Section(magazine)
                    magazine.sections.append(section)
                article=Article(section,magazine)
                article.name=e.find_by_xpath('dt/a').first.text
                article.url=e.find_by_xpath('dt/a').first['href']
                section.articles.append(article)
                logger.debug('found article %s at %s' % (article.name,article.url))
                articles.append(article)

        
        magazine.preSave()
        magazine.saveEpubMetadata()
        magazine.saveIndex()
        for s in magazine.sections:
            s.save()
            
        
        for a in articles:            
            logger.debug('download %s start ' % a.name) 
            self.downloadSingleArticle(a)
            logger.debug('download %s finish' % a.name)
        magazine.genEpub() 
        return magazine
        

    


    def downloadSingleArticle(self,article):
        browser=self.browser
        logger.debug('open article at %s' % article.url)
        browser.visit(article.url)
        logger.debug('open ok')
        imageElement=browser.find_by_css('div.articlePicBox img')
        if (len(imageElement)):
            article.imgUrl=browser.find_by_css('div.articlePicBox img').first['src']
            logger.debug('find article image at %s' % article.imgUrl)
        else:
            article.imgUrl=''
        browser.find_by_css('#the_content').first.text
        article.content=self.getArticleContent()
        pagesElement=browser.find_by_css('div.pulic_page li')
        if (len(pagesElement)):
            logger.debug('find pagenation')
            urls=[e.find_by_css('a').first['href'] for e in pagesElement[2:-3] ]
            for url in urls:
                logger.debug('go to %s' % url)
                browser.visit(url)                
                article.content=article.content+self.getArticleContent()
        article.save()
        

    def getArticleContent(self):
        browser=self.browser
        seleniumElement=browser.find_by_css('#the_content').first._element
        seleniumDriver=browser.driver
        return seleniumDriver.execute_script('return arguments[0].innerHTML',seleniumElement)

    def quit(self):
        self.browser.quit()



def main():
    magazines=['http://www.qikan.com.cn/MastMagazineArchive/1672-8335.html','http://www.qikan.com.cn/MastMagazineArchive/1673-2456.html']
    downloader = QiKanDownloader()
    try:
        downloader.login(),
        for m in magazines:
            downloader.download(m)
        print "done"
    finally:
        downloader.quit()

if __name__ == '__main__':
    main()
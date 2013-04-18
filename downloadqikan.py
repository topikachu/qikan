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
import pinyin
logging.basicConfig()
logger=logging.getLogger('qikan.Dowloader')


class Saver():
    def __init__(self,magazine):
        self.magazine=magazine
    def saveUTF8(self,filename,content,):
        f=codecs.open(os.path.join(self.magazine.destFolder(),filename),'w','utf-8')
        f.write(content)
        f.close()
    def saveImage(self,url,filename):
        req=urllib2.Request(url)
        req.add_header("Referer",self.magazine.url)
        r=urllib2.urlopen(req)
        f=open(os.path.join(self.magazine.destFolder(),filename),"wb")
        f.write(r.read())
        f.close()
        logger.debug('save %s to %s' % (url,filename))


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
        return os.path.join('workspace',pinyin.get(self.name+self.description))

    def preSave(self):
        idx=1
        self.sections=[s for s in self.sections if len(s.articles)]
        for s in self.sections:
            if not s.name:
                s.name="Section" 
            s.location="section%d.html" % idx
            s.id="id%d" % idx
            s.idx=idx
            idx=idx+1
            for a in s.articles:
                a.location="article%d.html" % idx
                a.id="id%d" % idx
                a.idx=idx
                
                idx=idx+1
        dest=self.destFolder()
        if (os.path.isdir(dest)):
            shutil.rmtree(dest, ignore_errors=True)
        shutil.copytree('template',dest)
        logger.debug("prepare target folder %s" % dest)
   
    def getEpubPath(self):
        return self.destFolder()+'.epub'
    def genEpub(self):
        self.saveUTF8('content.opf',Magazine.opfT.render_unicode(magazine=self))                
        self.saveUTF8('toc.ncx',Magazine.tocT.render_unicode(magazine=self))
        self.saveUTF8('index.html',Magazine.indexT.render_unicode(magazine=self))
        logger.debug('save epub metadata')
        if (self.cover):
            self.saveImage(self.cover,"cover.jpg")                        
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
        self.imgUrls=[]
        self.images=[]        
        Saver.__init__(self,magazine)
    def save(self):
        idx=0
        for imgUrl in self.imgUrls:
            imgLocation="img%d-%d.jpg" % (self.idx,idx)
            imgId="img%d-%d" % (self.idx,idx)
            self.saveImage(imgUrl, imgLocation)
            self.images.append((imgLocation,imgId))            
            logger.debug("download img OK")
            idx=idx+1
        self.saveUTF8(self.location,Article.articleT.render_unicode(article=self),)
        logger.debug('save article %s' % self.name)

class QiKanDownloader():
    def __init__ (self):
        #self.browser=Browser(profile='C:/Users/pikachu/AppData/Roaming/Mozilla/Firefox/Profiles/odfwln6i.default')
        self.browser=Browser()
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
            return self.downloadDetail(detail.first['href'])
        else:
            logger.debug('no detail')
    def downloadDetail(self,detailUrl):        
        logger.debug('detail download start')
        browser=self.browser
        magazine=Magazine()
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
                if not e.text.strip():
                    continue
                section=Section(magazine)
                section.name=e.text
                magazine.sections.append(section)
                logger.debug('found section %s' % section.name)
            else:                
                article=Article(section,magazine)
                nameEle=e.find_by_xpath('dt/a')
                if (not len(nameEle)):
                    continue
                article.name=e.find_by_xpath('dt/a').first.text
                article.url=e.find_by_xpath('dt/a').first['href']
                if ('section' not in vars()):
                    section=Section(magazine)
                    magazine.sections.append(section)
                section.articles.append(article)
                logger.debug('found article %s at %s' % (article.name,article.url))
                articles.append(article)        
        magazine.preSave() 
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
            self.findArticleAllImages(article)
           
        else:
            article.imgUrl=''
        article.content=''
        if browser.is_element_present_by_css('#the_content',10):
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
        

    def findArticleAllImages(self,article):
        browser=self.browser
        browser.find_by_css('div.articlePicBox img').first.click()
        while (True):
            if browser.is_element_present_by_css('img#lightboxImage',10):
                imgUrl=browser.find_by_css('img#lightboxImage').first['src']
                article.imgUrls.append(imgUrl)
                logger.debug('find article image at %s' % imgUrl)
                import time
                time.sleep(5)
                if (browser.is_element_present_by_css('a#nextLinkBottom',10) and browser.find_by_css('a#nextLinkBottom').first.visible):
                    browser.find_by_css('a#nextLinkBottom').first.click()
                else:
                    break
            else:
                break
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
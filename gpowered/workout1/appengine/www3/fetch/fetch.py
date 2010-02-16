from BeautifulSoup import BeautifulSoup
import os
import sys
import re
import wsgiref.handlers
from google.appengine.api import urlfetch
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
import htmllib, formatter
import sgmllib
from models import Img
from google.appengine.ext import db

_DEBUG = True

class BaseRequestHandler(webapp.RequestHandler):

    def generate(self, template_name, template_values={}):
        values = {}
        values.update(template_values)
        directory = os.path.dirname(__file__)
        path = os.path.join(directory, 'templates', template_name)
        self.response.out.write(template.render(path, values, debug=_DEBUG))


class MainHandler(BaseRequestHandler):
    def get(self):
        url = 'http://www.google.com'
        result = urlfetch.fetch(url)
        format = formatter.NullFormatter()           # create default formatter
        htmlparser = LinksExtractor(format, url)        # create new parser objectbject
        htmlparser.feed(result.content)
        htmlparser.close()
        links = htmlparser.get_links()
        imgs = htmlparser.get_imgs()
        self.generate('base.html', template_values={'url': url,
                                                    'page': result.content,
                                                    'links': links,
                                                    'imgs': imgs
                                                    })
        
    #def get_url(self, orrig):
class MainHandler2(BaseRequestHandler):
    url = None
    foo = None
    def my_blob(self, img):
        loc = img.find('http:')
        if loc < 0 or loc > 6:
            if img[0] != '/':
                img = '%s/1%s' % (self.url, img)
            else:
                #img = '%s%s' % (self.url, img)
                loc2 = img.find('//')
                if loc2 < 0:
                    img = '%s%s' % (self.url, img)
                else:
                    img = 'http://google.com/%s/%s' % (self.url.split('//')[1].split('/'), img)
        test = getImg(img)
        if not test:
            store = Img(url=img)
            store.picture = db.Blob(urlfetch.Fetch(img).content)
            store.put()
        pass_on = 'image?img=%s' % img
        return pass_on

    def scan_blobs(self, tag, type):
        for e in self.soup.findAll(tag):
            try:
                e['src'] = self.my_blob(e[type])
            except:
                pass
    def url_fix(self, tag, type):
        for a in self.soup.findAll(tag):
            try:
                href = a[type]
                loc = href.find('http')
                if loc < 0 or loc > 5:
                        if href[0] != '/':
                            href = '%s%s/%s' % ('?l=', self.url, href)
                        else:
                            href = '%s%s%s' % ('?l=', self.url, href)
                else:
                        href = '%s%s' % ('?l=', href)
                a['href'] = href
            except:
                pass

    def start(self):
        self.generate('start.html', template_values={'url': self.foo,
                                            
                                            })
    def post(self):
        self.url = self.request.get('l')
        return self.get()
    
    def get(self):
        #if not self.url:
        self.url = self.request.get('l')
        if not self.url:
            return self.start()
        loc = self.url.find('http')
        if loc < 0 or loc > 5:
            self.url = 'http://%s' % self.url
        result = urlfetch.fetch(self.url)
        self.soup = BeautifulSoup(result.content)
    #print soup.prettify()
        self.scan_blobs('img', 'src')
        self.scan_blobs('script', 'src')
        self.scan_blobs('style', 'src')
        self.url_fix('a', 'href')
        self.url_fix('link', 'href')
        
    
            
        for a in self.soup.findAll('form'):
            try:
                href = a['action']
                loc = href.find('http')
                if loc < 0 or loc > 5:
                        if href[0] != '/':
                            href = '%s%s/%s' % ('?l=', self.url, href)
                        else:
                            href = '%s%s%s' % ('?l=', self.url, href)
                else:
                        href = '%s%s' % ('?l=', href)
                a['action'] = href
                self.foo = a['action']
            except:
                pass            

        self.generate('base.html', template_values={'url': self.url,
                                            'page': self.soup.prettify(),
                                            #'links': links,
                                            #'imgs': imgs
                                            })


        
class GetImage(webapp.RequestHandler):
    def get(self):
        url = self.request.get('img')
        img = getImg(url)
        if (img and img.picture):
            self.response.headers['Content-Type'] = 'image/jpg'
            self.response.out.write(img.picture)
        else:
            self.redirect('/static/noimage.jpg')
    
def getImg(url):
    result = db.GqlQuery("SELECT * FROM Img WHERE url = :1 LIMIT 1", url).fetch(1)
    if (len(result) > 0):
        return result[0]
    else:
        return None
            
            
def main():
    application = webapp.WSGIApplication([('/', MainHandler2),
                                          ('/image', GetImage),
                                      ],
                                      debug=True)
    wsgiref.handlers.CGIHandler().run(application)


if __name__ == '__main__':
    main()

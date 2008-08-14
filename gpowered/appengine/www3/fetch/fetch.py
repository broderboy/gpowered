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
            

#class LinksExtractor(htmllib.HTMLParser): # derive new HTML parser
class LinksExtractor(sgmllib.SGMLParser): # derive new HTML parser

    def __init__(self, formatter, url) :        # class constructor
        self.url = url
        htmllib.HTMLParser.__init__(self, formatter)  # base class constructor
        self.links = []        # create an empty list for storing hyperlinks
        self.imgs = []

    def start_a(self, attrs) :  # override handler of <A ...>...</A> tags
        # process the attributes
        if len(attrs) > 0 :
            for attr in attrs :
                if attr[0] == "href":         # ignore all non HREF attributes
                    link = attr[1]
                    loc = link.find('http:')
                    if loc < 0 or loc > 6:
                        if link[0] != '/':
                            link = '%s/%s' % (self.url, link)
                        else:
                            link = '%s%s' % (self.url, link)
                    self.links.append(link) # save the link info in the list

    def start_img(self, attrs):
        if len(attrs) > 0 :
            for attr in attrs :
                if attr[0] == "src":
                    img = attr[1]
                    loc = img.find('http:')
                    if loc < 0 or loc > 6:
                        if img[0] != '/':
                            img = '%s/%s' % (self.url, img)
                        else:
                            img = '%s%s' % (self.url, img)
                    test = getImg(img)
                    if not test:
                        store = Img(url=img)
                        store.picture = db.Blob(urlfetch.Fetch(img).content)
                        store.put()
                    pass_on = 'image?img=%s' % img
                    replace = {'src': pass_on}
                    #attr.update(replace)
                    attr.setattr(attr, 'src', pass_on)
                    #attr = ('src',) + (pass_on,) 
                    self.imgs.append(attr)
                if attr[0] == "alt":
                    attr = ('alt',) + ('moo',) 
    
    def get_links(self):     # return the list of extracted links
        return self.links   
    
    def get_imgs(self):
        return self.imgs        
            
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
    application = webapp.WSGIApplication([('/', MainHandler),
                                          ('/image', GetImage),
                                      ],
                                      debug=True)
    wsgiref.handlers.CGIHandler().run(application)


if __name__ == '__main__':
    main()

import wsgiref.handlers
from google.appengine.api import urlfetch
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext import db
import os, re

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
    msg = self.request.get('msg')
    url = 'http://google.com/complete/search?q=%s' % msg
    result = urlfetch.fetch(url)
    terms = re.findall('"(.*?)",?', result.content)
    i = 1
    f = []
    while i < len(terms):
        f.append(terms[i])
        i = i + 3

    
    
      
    self.generate('base.html', template_values={'urchin': True,
                                                'url': url,
                                                'terms': terms,
                                                'result': f
                                                })

def main():
  application = webapp.WSGIApplication([('/', MainHandler),
                                       ],
                                       debug=True)
  wsgiref.handlers.CGIHandler().run(application)



if __name__ == '__main__':
  main()
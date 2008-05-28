import os, sys, re

import wsgiref.handlers
from models import Account, RsaKey

from google.appengine.ext import webapp
from google.appengine.api import users
from google.appengine.ext.webapp import template
from google.appengine.api import urlfetch
import simplejson
import rsa

_DEBUG = True

class BaseRequestHandler(webapp.RequestHandler):
  
  def generate(self, template_name, template_values={}):
    user = users.get_current_user()
    
    if user:
      log_in_out_url = users.create_logout_url('/')
    else:
      log_in_out_url = users.create_login_url(self.request.path)
    
    values = {'user': user, 'log_in_out_url': log_in_out_url}
    values.update(template_values)
    directory = os.path.dirname(__file__)
    path = os.path.join(directory, 'templates', template_name)
    self.response.out.write(template.render(path, values, debug=_DEBUG))
    
class MainHandler(BaseRequestHandler):

  def get(self):
    self.generate('base.html', template_values={'urchin': True})
    
class SettingsHander(BaseRequestHandler):

    def get(self):
        current_user = users.get_current_user()        
        if not current_user:
            self.redirect(users.create_login_url(self.request.path))
        twitter = None
        user = Account.gql('WHERE user = :1', current_user).get()
        
        if user:
            twitter = user.twitter        
        
        self.generate('settings.html', template_values={'user': current_user,
                                                        'twitter': twitter,
                                                        'urchin': True,
                                                })
    def post(self):
        current_user = users.get_current_user()        
        if not current_user:
            self.redirect(users.create_login_url(self.request.path))
        
        password = self.request.get('password')
        twitter = self.request.get('twitter')
        active = self.request.get('active')
        
        errors = []
        
        if not password:
            errors.append('Password must be filled in')
        if not twitter:
            errors.append('Twitter Account must be filled in')
        
        if len(errors) == 0:
            user = Account.gql('WHERE user = :1', current_user).get()
            if not user:
                user = Account(user=current_user, gPass=password, twitter=twitter, active=True, counts=0)
            else:
                user.gLogin = current_user.nickname().replace(' ', '')
                user.gPass = password
                user.twitter = twitter
                user.active = True
                
            
            user.put()
            errors = None
        
        self.generate('settings.html', template_values={'user': current_user,
                                                        'errors': errors,
                                                        'urchin': True,
                                                })
class TweetHander(BaseRequestHandler):
        
    def makePubKey(self, k):
        temp = k.split('!')
        pubkey = {'e': long(temp[0]), 'n': long(temp[1])}
        return pubkey
    
    def makePrivKey(self, k):
        temp = k.split('!')
        privkey = {'d': long(temp[0]), 'p': long(temp[1]), 'q': long(temp[2])}        
        return privkey        
    
    def getTwitterStatus(self, username):
        twitter_url = 'http://twitter.com/statuses/user_timeline/%s.json?count=1'
        url = twitter_url % username

        result = urlfetch.fetch(url)
            
        json = simplejson.loads(str(result.content))
        try:    
            return json[0].get('text')  
        except:
            return 'twitter account is wrong in twitter2gTalk'
    
    def encryptGtalk(self, email, password, msg):   
        gp_pub = RsaKey.gql("WHERE name = :1", 'gp_pub').get()
        gae_priv = RsaKey.gql("WHERE name = :1", 'gae_priv').get()
           
        gpowered_gtalk_url = 'http://gpowered.net/g/gtalk/update/%s/'
        
        enc = '%s!gpowered!%s!gpowered!%s' % (email, password, msg)
        
        gp_pubkey = self.makePubKey(gp_pub.keystring)
        gae_privkey = self.makePrivKey(gae_priv.keystring)        
        
        gae_one = rsa.encrypt(str(enc), gp_pubkey)
        #gae_two = rsa.sign(gae_one, gae_privkey)
        
        encrypted_url = gpowered_gtalk_url % gae_one.replace('/', '!GP!')
        
        return encrypted_url
    
    def get(self):        
        user = Account.gql('WHERE gLogin = :1 ', self.request.get('u')).get()
        
        count = 0
        results = []
        #for user in users:
        if user.twitter and user.user and user.gPass:
            twitter_status = None        
            twitter_status = self.getTwitterStatus(user.twitter) 
            
            email = '%s@gmail.com' % user.user
            
            gpowered_url = self.encryptGtalk(email, user.gPass, twitter_status)
            
            result = urlfetch.fetch(re.sub("\s+", "%20", str(gpowered_url)))
            results.append(result) 
            user.counts = user.counts + 1
            user.put()    
            count = count + 1

        self.generate('update.html', template_values={
                                                   'names': users,
                                                   'count' : count,
                                                   'results' : results,
                                                })
                                                
class ListHandler(BaseRequestHandler):

    def makePubKey(self, k):
        temp = k.split('!')
        pubkey = {'e': long(temp[0]), 'n': long(temp[1])}
        return pubkey
    
    def makePrivKey(self, k):
        temp = k.split('!')
        privkey = {'d': long(temp[0]), 'p': long(temp[1]), 'q': long(temp[2])}        
        return privkey 

    def get(self):
        gp_pub = RsaKey.gql("WHERE name = :1", 'gp_pub').get()
        gae_priv = RsaKey.gql("WHERE name = :1", 'gae_priv').get()
        gp_pubkey = self.makePubKey(gp_pub.keystring)
        gae_privkey = self.makePrivKey(gae_priv.keystring)
        
        ret = ''
        users = Account.gql('WHERE active = :1 ', True)
        
        for user in users:
        	ret = ret + '%s!gp!%s!gp!%s!GP!' % (user.user, user.gPass, user.twitter)
        
        gae_one = rsa.encrypt(str(ret), gp_pubkey)
        
        self.generate('list.html', template_values={'users': gae_one})

def main():
  application = webapp.WSGIApplication([('/', MainHandler),
                                       ('/settings/', SettingsHander),
                                       ('/save/', SettingsHander),
                                       ('/update/', TweetHander),
                                       ('/list/', ListHandler),
                                       ],
                                       debug=True)
  wsgiref.handlers.CGIHandler().run(application)



if __name__ == '__main__':
  main()

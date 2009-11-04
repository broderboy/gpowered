from django.http import HttpResponse
import datetime
import logging


import sys, xmpp, os, urllib2, time, simplejson
from time import gmtime, strftime

from service.models import *
from rsa.models import *
import crypt

class Twitter2gChat:
    
    def __init__(self):
        self.twitter_service = Service.objects.get(name='Twitter')
        twitter_service_login = self.twitter_service.servicelogin_set.all()[:1][0]
        
        self.ts_login = twitter_service_login.username
        self.ts_pass = twitter_service_login.password
    
        self.twitter_status = None
        self.updated = None
        self.catches = 0
    
    #keep looping and wait for xmpp response
    def GoOn(self,conn):
        while self.StepOn(conn):
            pass
    
    #keep listening for responses
    def StepOn(self,conn):
        print 'StepOn'
        if self.updated:
            return 0
        try:
            conn.Process(1)
        except KeyboardInterrupt:
            return 0
        return 1

    #handle responses
    def iqHandler(self, conn,iq_node):
        print 'in iqHandler'
        print strftime("%a, %d %b %Y %H:%M:%S +0000", gmtime())
        self.catches = self.catches + 1
        
        #we have looped enough, die
        if self.catches == 4:
            print 'i think we did it'
            #sys.exit(0)
            self.updated = True
            return
        
        #print response, don't need to send anything back    
        if self.updated == True:
            try:
                print iq_node
            except:
                pass
        
        #havn't updated yet, sent status update
        else:
            #we can build of response
            node = iq_node.getChildren()[0]
            
            #remove what we don't ned
            node.delAttr('status-list-max')
            node.delAttr('status-max')
            node.delAttr('status-list-contents-max')
            iq_node.delAttr('from')
            iq_node.delAttr('type')
            iq_node.delAttr('to')
           
           #update the current status

            try:
                curr_status = node.getChildren()[0]
                print curr_status
            except IndexError:
                curr_status = node
                curr_status.setData('twitter2gTalk will not work with protected tweets')
            
            #no need to update
            if curr_status.getData() == self.twitter_status:
                print 'status is already tweet'
                #sys.exit(0)
                self.updated = True
                
            curr_status.setData(self.twitter_status)

            #set response
            iq_node.setType('set')
            
            print 'sending'
            try:
                print iq_node
            except:
                pass
            self.updated = True
            conn.send(iq_node)
            print 'end of iqHandler\n\n'

    #start talking to the server and update status
    def updateGtalkStatus(self, google_username, google_pass):
        if '@' not in google_username:
            google_username = '%s@gmail.com' % google_username
        print google_username
        #connect
        jid=xmpp.protocol.JID(google_username)
        cl=xmpp.Client(jid.getDomain(),debug=[])
        if not cl.connect(('talk.google.com',5222)):
            print 'Can not connect to server.'
            #sys.exit(1)
            self.updated = True
            return
        if not cl.auth(jid.getNode(),google_pass):
            print 'Can not auth with server %s ' % google_username
            self.updated = True
            return 
            
        #build query to get current status
        iq = xmpp.Iq()
        iq.setType('get')
        iq.setTo(google_username)

        node = xmpp.Node()
        node.setName('query')
        node.setAttr('xmlns', 'google:shared-status')

        iq.addChild(node=node) 
        print iq

        #register with server and send subscribe to status updates
        cl.RegisterHandler('iq',self.iqHandler)
        cl.send(iq)

        self.GoOn(cl)
        cl.disconnect()
        
    #get current twitter status
    def getTwitterStatus(self, username):
        twitter_url = 'http://twitter.com/statuses/user_timeline/%s.json?count=1'
        url = twitter_url % username
        print url
        try:
            f = urllib2.urlopen(url)
            result = f.read()
            
            json = simplejson.loads(str(result))
    
            return json[0].get('text')
        except urllib2.HTTPError:
            print 'urllib2.HTTPError'
            return ''
        except IndexError:
            print 'IndexError'
            return ''
        except ValueError:
            print 'no account'
            return ''

    def makePubKey(self, k):
        temp = k.split('!')
        pubkey = {'e': long(temp[0]), 'n': long(temp[1])}
        return pubkey

    def makePrivKey(self, k):
        temp = k.split('!')
        print "k %s" % k
        privkey = {'d': long(temp[0]), 'p': long(temp[1]), 'q': long(temp[2])}        
        return privkey    
    
    def getlogger(self):
        logger = logging.getLogger()
        hdlr = logging.FileHandler('TIMLOG.txt')
        formatter = logging.Formatter('[%(asctime)s]%(levelname)-8s"%(message)s"','%Y-%m-%d %a %H:%M:%S') 
        
        hdlr.setFormatter(formatter)
        logger.addHandler(hdlr)
        logger.setLevel(logging.NOTSET)
    
        return logger

    def loop(self, slug):
        gae_pub = RsaKey.objects.get(name="gae_pub").key
        gp_priv = RsaKey.objects.get(name="gp_priv").key
        gp_privkey = self.makePrivKey(gp_priv)
        gae_pubkey = self.makePubKey(gae_pub)

        gtalk_service = Service.objects.get(name='google')

        enc = crypt.decrypt(slug, gp_privkey)
        print "DECR %s" % enc
        decrypted = enc.split('!gp!')

        gLogin = decrypted[0]
        gPass = decrypted[1]
        twit = decrypted[2]
        
        self.logger = self.getlogger()
        self.logger.error("HIIIiiii %s" % gLogin)
        print "HIIIiiii %s" % gLogin
        
        self.twitter_status = ''
        self.updated = None
        self.catches = 0

        self.twitter_status = self.getTwitterStatus(twit)
        try:
            print self.twitter_status
        except:
            pass

        if self.twitter_status != '' and '@' not in self.twitter_status:

            self.updateGtalkStatus(gLogin, gPass)
        else:
            self.updated = True             

        while not self.updated:
            print self.updated
            time.sleep(2)


def start(request, slug):
    now = datetime.datetime.now()
    html = "<html><body>It is now %s.</body></html>" % now
    slug = slug.replace('!gp!', '\n')
    t = Twitter2gChat()
    t.loop(slug)
    return HttpResponse(html)

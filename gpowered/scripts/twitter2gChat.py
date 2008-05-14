############
from django.core.management import setup_environ
import sys
sys.path.append('/home/broderboy/workspace/')
sys.path.append('/home/gpowered/gpowered-read-only/')
from gpowered import settings

setup_environ(settings)

############

from gpowered.core.models import ServiceLogin, Service
import sys, xmpp, os, twitter
from time import gmtime, strftime

class Twitter2gChat:
    
    def __init__(self):
        self.twitter_service = Service.objects.get(name='Twitter')
        twitter_service_login = self.twitter_service.servicelogin_set.all()[:1][0]
        
        self.ts_login = twitter_service_login.username
        self.ts_pass = twitter_service_login.password
    
        self.twitter_status = None
        self.updated = False
        self.catches = 0
    
    #keep looping and wait for xmpp response
    def GoOn(self,conn):
        while self.StepOn(conn):
            pass
    
    #keep listening for responses
    def StepOn(self,conn):
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
            sys.exit(0)
        
        #print response, don't need to send anything back    
        if self.updated == True:
            print iq_node
        
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
            curr_status = node.getChildren()[0]
            
            #no need to update
            if curr_status.getData() == self.twitter_status:
                print 'status is already tweet'
                sys.exit(0)
                
            curr_status.setData(self.twitter_status)

            #set response
            iq_node.setType('set')
            
            print 'sending'
            print iq_node
            self.updated = True
            conn.send(iq_node)
            print 'end of iqHandler\n\n'

    #start talking to the server and update status
    def updateGtalkStatus(self, google_username, google_pass):
        
        #connect
        jid=xmpp.protocol.JID(google_username)
        cl=xmpp.Client(jid.getDomain(),debug=[])
        if not cl.connect(('talk.google.com',5222)):
            print 'Can not connect to server.'
            sys.exit(1)
        if not cl.auth(jid.getNode(),google_pass):
            print 'Can not auth with server'
            sys.exit(1)
            
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
        api = twitter.Api(username=self.ts_login, password=self.ts_pass)
        twitter_status = api.GetUserTimeline(username, 1)[0].text
        
        #don't want to use replies
        if twitter_status.find('@') == 0:
            return ''
        else:
            return twitter_status
    
    def loop(self):
        gtalk_service = Service.objects.get(name='google')
        for user in self.twitter_service.users.all():
    
            try:
                twitter_account =  user.extaccount_set.get(service=self.twitter_service)
                google_account =  user.extaccount_set.get(service=gtalk_service)

                self.twitter_status = self.getTwitterStatus(twitter_account.username)
                
                if self.twitter_status != '':
                    self.updateGtalkStatus(google_account.username, google_account.password)
                
            except:
                pass

t = Twitter2gChat()
t.loop()
#t.getTwitterStatus()
#t.updateGtalkStatus()

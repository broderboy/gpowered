# Create your views here

import xmpp,sys
from django.shortcuts import render_to_response
import rsa
from gpowered.core.models import RsaKey

class gTalkStatus:    
    def __init__(self, username, password, msg):
        self.username = username
        self.password = password
        self.twitter_status = msg
        self.updated = False
        self.catches = 0
        
    #keep looping and wait for xmpp response
    def GoOn(self,conn):
        while self.StepOn(conn):
            if(self.updated):
                return
            pass
    
    #keep listening for responses
    def StepOn(self,conn):
        if(self.updated):
            return
        
        try:
            conn.Process(1)
        except KeyboardInterrupt:
                return 0
        return 1

    #handle responses
    def iqHandler(self, conn,iq_node):
        if(self.updated):
            return
        print 'in iqHandler'
        self.catches = self.catches + 1
        
        #we have looped enough, die
        if self.catches == 4:
            print 'i think we did it'
            #sys.exit(0)
            return
            return render_to_response('gtalk/gtalk.html', 
                          {    
                           'login': self.username,
                           'password': self.password,
                           'msg': self.twitter_status,
                           })
        
        #print response, don't need to send anything back    
        if self.updated == True:
            print iq_node
        
        #havn't updated yet, sent status update
        else:
            #we can build of response
            node = iq_node.getChildren()[0]
            #return render_to_response('gtalk/gtalk.html', 
            #              {    
            #               'debug': node,
            #               })
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
            #TODO
            #if curr_status.getData() == self.twitter_status:
            #    print 'status is already tweet'
            #    sys.exit(0)
                #self.__del__()
                #return
            #    return render_to_response('gtalk/gtalk.html', 
            #              {    
            #               'login': self.username,
            #               'password': self.password,
            #               'msg': self.twitter_status,
            #               }                
                
            curr_status.setData(self.twitter_status)

            #set response
            iq_node.setType('set')
            
            print 'sending'
            print iq_node
            self.updated = True
            conn.send(iq_node)
            print 'end of iqHandler\n\n'

    #start talking to the server and update status
    def updateGtalkStatus(self):
        #connect
        jid=xmpp.protocol.JID(self.username)
        cl=xmpp.Client(jid.getDomain(),debug=[])
        if not cl.connect(('talk.google.com',5222)):
            print 'Can not connect to server.'
            return render_to_response('gtalk/gtalk.html', 
                          {    
                           'error': 'could not connect to server',
                           })
        if not cl.auth(jid.getNode(),self.password):
            print 'Can not auth with server'
            return render_to_response('gtalk/gtalk.html', 
                          {    
                           'error': 'coult not auth with server',
                           })
            
        #build query to get current status
        iq = xmpp.Iq()
        iq.setType('get')
        iq.setTo(self.username)

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

#def status_update(request, login, password, msg):

def makePubKey(k):
    temp = k.split('!')
    pubkey = {'e': long(temp[0]), 'n': long(temp[1])}
    return pubkey

def makePrivKey(k):
    temp = k.split('!')
    privkey = {'d': long(temp[0]), 'p': long(temp[1]), 'q': long(temp[2])}        
    return privkey

def status_update(request, url):
    
    url = url.replace('!GP!', '/')
    
    gae_pub = RsaKey.objects.filter(name="gae_pub")[0].key
    gp_priv = RsaKey.objects.filter(name="gp_priv")[0].key
    
    gp_privkey = makePrivKey(gp_priv)
    gae_pubkey = makePubKey(gae_pub)
    
    gp_one = rsa.verify(url, gae_pubkey)
    enc = rsa.decrypt(gp_one, gp_privkey)
    
    encs = enc.split('!gpowered!')
    login = encs[0]
    password = encs[1]
    msg = encs[2]
    t = gTalkStatus(login,password,msg)
    t.updateGtalkStatus()
    return render_to_response('gtalk/gtalk.html', 
                              {    
                               'login': login,
                               'password': password,
                               'msg': msg,
                               })
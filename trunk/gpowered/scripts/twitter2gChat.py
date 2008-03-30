import sys, xmpp, os, twitter

class Twitter2gChat:
    
    twitter_login = os.environ['TWITTER_LOGIN']
    twitter_pass = os.environ['TWITTER_PASS']
    google_login = os.environ['GOOGLE_LOGIN']
    google_pass = os.environ['GOOGLE_PASS']

    twitter_status = None
    updated = False
    catches = 0
    
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
    def updateGtalkStatus(self):
        
        #connect
        jid=xmpp.protocol.JID(self.google_login)
        cl=xmpp.Client(jid.getDomain(),debug=[])
        if not cl.connect(('talk.google.com',5222)):
            print 'Can not connect to server.'
            sys.exit(1)
        if not cl.auth(jid.getNode(),self.google_pass):
            print 'Can not auth with server'
            sys.exit(1)
            
        #build query to get current status
        iq = xmpp.Iq()
        iq.setType('get')
        iq.setTo('timothy.broder@gmail.com')

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
    def getTwitterStatus(self):
        api = twitter.Api(username=self.twitter_login, password=self.twitter_pass)
        self.twitter_status = api.GetUserTimeline(self.twitter_login, 1)[0].text
        
        #don't want to use replies
        if self.twitter_status.find('@') >= 0:
            sys.exit(0)

t = Twitter2gChat()
t.getTwitterStatus()
t.updateGtalkStatus()

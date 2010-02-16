from django.db import models
from django.contrib.auth.models import User

class Service(models.Model):
    name = models.CharField(max_length=32)
    users = models.ManyToManyField(User)
    url = models.CharField(max_length=64)
    is_external = models.BooleanField()
    
    def __unicode__(self):
        return self.name

    
class ExtAccount(models.Model):
    user = models.ForeignKey(User)
    service = models.ForeignKey(Service)
    username = models.CharField(max_length=32)
    password = models.CharField(max_length=32,blank=True, null=True)
    profile_url = models.CharField(max_length=64,blank=True, null=True)
    
    def __unicode__(self):
        return '%s: %s' % (self.user, self.service.name)

    
class ServiceLogin(models.Model):
    service = models.ForeignKey(Service)
    username = models.CharField(max_length=32)
    password = models.CharField(max_length=32,blank=True, null=True)
    
    def __unicode__(self):
        return self.service.name

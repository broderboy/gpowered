from django.db import models
from django.contrib.auth.models import User

class Service(models.Model):
    name = models.CharField(maxlength=32)
    users = models.ManyToManyField(User)
    url = models.CharField(maxlength=64)
    is_external = models.BooleanField()
    
    def __str__(self):
        return self.name
    
    class Admin:
        pass
    
class ExtAccount(models.Model):
    user = models.ForeignKey(User)
    service = models.ForeignKey(Service)
    username = models.CharField(maxlength=32)
    password = models.CharField(maxlength=32,blank=True, null=True)
    profile_url = models.CharField(maxlength=64,blank=True, null=True)
    
    def __str__(self):
        return '%s: %s' % (self.user, self.service.name)
    
    class Admin:
        pass
    
class ServiceLogin(models.Model):
    service = models.ForeignKey(Service)
    username = models.CharField(maxlength=32)
    password = models.CharField(maxlength=32,blank=True, null=True)
    
    def __str__(self):
        return self.service.name
    
    class Admin:
        pass
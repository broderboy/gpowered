from django.db import models

class RsaKey(models.Model):
    name = models.CharField(max_length=32)
    key = models.CharField(max_length=512)
    
    def __unicode__(self):
        return self.name
    
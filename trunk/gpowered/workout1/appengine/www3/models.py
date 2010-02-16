from google.appengine.ext import db

class Img(db.Model):
    url = db.StringProperty(required = True)
    picture = db.BlobProperty(default=None)

